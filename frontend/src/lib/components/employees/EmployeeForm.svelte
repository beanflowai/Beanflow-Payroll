<script lang="ts">
	import { untrack } from 'svelte';
	import type { Employee, Province, VacationPayoutMethod, VacationRate, VacationRatePreset, EmployeeCreateInput, EmployeeUpdateInput, PayFrequency, EmploymentType, EmployeeTaxClaim } from '$lib/types/employee';
	import {
		PROVINCE_LABELS,
		PAY_FREQUENCY_LABELS,
		EMPLOYMENT_TYPE_LABELS,
		VACATION_RATE_LABELS,
		FEDERAL_BPA_2025,
		PROVINCIAL_BPA_2025,
		PROVINCES_WITH_EDITION_DIFF,
		calculateYearsOfService,
		suggestVacationRate,
		getVacationRatePreset
	} from '$lib/types/employee';
	import { getBPADefaults, getBPADefaultsByYear, getContributionLimits, type BPADefaults, type ContributionLimits } from '$lib/services/taxConfigService';
	import { getVacationRates, getProvinceStandards, type VacationRatesConfig, type ProvinceStandards } from '$lib/services/configService';
	import { createEmployee, updateEmployee, checkEmployeeHasPayrollRecords, getEmployeeTaxClaims, createEmployeeTaxClaimViaApi, updateEmployeeTaxClaimViaApi } from '$lib/services/employeeService';
	import TaxYearClaimsCard from './TaxYearClaimsCard.svelte';

	interface Props {
		employee?: Employee | null;
		mode: 'create' | 'edit';
		onSuccess: (employee: Employee) => void;
		onCancel: () => void;
	}

	let { employee = null, mode, onSuccess, onCancel }: Props = $props();

	// Form state
	let firstName = $state(employee?.firstName ?? '');
	let lastName = $state(employee?.lastName ?? '');
	let sin = $state(''); // Only used in create mode
	let email = $state(employee?.email ?? '');
	// Address fields
	let addressStreet = $state(employee?.addressStreet ?? '');
	let addressCity = $state(employee?.addressCity ?? '');
	let addressPostalCode = $state(employee?.addressPostalCode ?? '');
	let occupation = $state(employee?.occupation ?? '');
	let province = $state<Province>(employee?.provinceOfEmployment ?? 'ON');
	let payFrequency = $state<PayFrequency>(employee?.payFrequency ?? 'bi_weekly');
	let employmentType = $state<EmploymentType>(employee?.employmentType ?? 'full_time');
	let hireDate = $state(employee?.hireDate ?? '');
	let tags = $state<string[]>(employee?.tags ?? []);
	let newTag = $state('');

	// Compensation
	let compensationType = $state<'salaried' | 'hourly'>(
		employee?.hourlyRate ? 'hourly' : 'salaried'
	);
	let annualSalary = $state(employee?.annualSalary ?? 0);
	let hourlyRate = $state(employee?.hourlyRate ?? 0);

	// Tax - Multi-year TD1 claims state
	// Tax years: current year and previous year
	const currentTaxYearForClaims = new Date().getFullYear(); // e.g., 2026
	const previousTaxYear = currentTaxYearForClaims - 1;       // e.g., 2025

	// Tax claims by year (loaded from DB in edit mode, initialized in create mode)
	let taxClaimsByYear = $state<Map<number, EmployeeTaxClaim>>(new Map());
	let taxClaimsLoading = $state(false);
	let bpaDefaultsByYear = $state<Map<number, BPADefaults>>(new Map());

	// Expand/collapse state for year cards
	let currentYearExpanded = $state(true);
	let previousYearExpanded = $state(false);

	// Legacy single-year state (for backward compatibility during transition)
	// These are still used for create mode and fallback
	let bpaDefaults = $state<BPADefaults | null>(null);
	let bpaLoading = $state(false);

	// Derived: Current BPA values (from API or fallback)
	const federalBPA = $derived(bpaDefaults?.federalBPA ?? FEDERAL_BPA_2025);
	const provincialBPA = $derived(bpaDefaults?.provincialBPA ?? PROVINCIAL_BPA_2025[province]);

	// Additional claims - now derived from taxClaimsByYear for current year
	let federalAdditionalClaims = $state(employee?.federalAdditionalClaims ?? 0);
	let provincialAdditionalClaims = $state(employee?.provincialAdditionalClaims ?? 0);
	let bpaRequestVersion = $state(0);
	let showProvinceChangeWarning = $state(false);
	// Track original province for detecting changes (Fix #3)
	let originalProvince = $state<Province | null>(employee?.provinceOfEmployment ?? null);
	let provinceChanged = $derived(mode === 'edit' && originalProvince !== null && province !== originalProvince);
	let isCppExempt = $state(employee?.isCppExempt ?? false);
	let isEiExempt = $state(employee?.isEiExempt ?? false);
	let cpp2Exempt = $state(employee?.cpp2Exempt ?? false);

	// Derived: Total claim amounts (BPA + additional claims)
	const federalClaimAmount = $derived(federalBPA + federalAdditionalClaims);
	const provincialClaimAmount = $derived(provincialBPA + provincialAdditionalClaims);

	// Fetch BPA when province changes (additional claims are stored directly, no recalculation needed)
	$effect(() => {
		const currentProvince = province;
		if (currentProvince) {
			bpaLoading = true;
			// Use untrack to avoid creating a dependency on bpaRequestVersion
			// Otherwise reading bpaRequestVersion would cause an infinite loop
			const requestVersion = untrack(() => ++bpaRequestVersion);
			getBPADefaults(currentProvince).then(defaults => {
				// Ignore stale responses from previous requests
				if (requestVersion !== bpaRequestVersion) return;
				bpaDefaults = defaults;
				bpaLoading = false;
			}).catch(() => {
				if (requestVersion !== bpaRequestVersion) return;
				// Fallback values are already set via $derived
				bpaLoading = false;
			});
		}
	});

	// Load tax claims for edit mode or initialize for create mode
	$effect(() => {
		if (mode === 'edit' && employee?.id) {
			loadTaxClaims(employee.id);
		} else if (mode === 'create') {
			initializeNewClaims();
		}
	});

	// Reload BPA defaults when province changes (for multi-year)
	$effect(() => {
		const currentProvince = province;
		if (currentProvince) {
			loadBpaDefaultsForYears(currentProvince);
		}
	});

	/**
	 * Load tax claims from database for an existing employee.
	 * Also initializes placeholder claims for any missing years.
	 */
	async function loadTaxClaims(employeeId: string) {
		taxClaimsLoading = true;
		try {
			// First ensure BPA defaults are loaded
			await loadBpaDefaultsForYears(province);

			const result = await getEmployeeTaxClaims(employeeId);
			const claimsMap = new Map<number, EmployeeTaxClaim>();

			// Load existing claims
			if (result.data) {
				for (const claim of result.data) {
					claimsMap.set(claim.taxYear, claim);
				}
			}

			// Initialize placeholder claims for any missing years (Fix #5)
			const years = [currentTaxYearForClaims, previousTaxYear];
			for (const year of years) {
				if (!claimsMap.has(year)) {
					const bpaForYear = bpaDefaultsByYear.get(year);
					claimsMap.set(year, {
						id: '', // Empty ID indicates new claim to be created
						employeeId: employeeId,
						companyId: '',
						taxYear: year,
						federalBpa: bpaForYear?.federalBPA ?? FEDERAL_BPA_2025,
						federalAdditionalClaims: 0,
						federalTotalClaim: bpaForYear?.federalBPA ?? FEDERAL_BPA_2025,
						provincialBpa: bpaForYear?.provincialBPA ?? PROVINCIAL_BPA_2025[province],
						provincialAdditionalClaims: 0,
						provincialTotalClaim: bpaForYear?.provincialBPA ?? PROVINCIAL_BPA_2025[province],
						createdAt: '',
						updatedAt: ''
					});
				}
			}

			taxClaimsByYear = claimsMap;

			// Also sync the legacy single-year state for backward compatibility
			const currentClaim = claimsMap.get(currentTaxYearForClaims);
			if (currentClaim) {
				federalAdditionalClaims = currentClaim.federalAdditionalClaims;
				provincialAdditionalClaims = currentClaim.provincialAdditionalClaims;
			}
		} catch (err) {
			console.error('Failed to load tax claims:', err);
		} finally {
			taxClaimsLoading = false;
		}
	}

	/**
	 * Initialize placeholder claims for a new employee
	 */
	async function initializeNewClaims() {
		await loadBpaDefaultsForYears(province);

		// Create placeholder claims using BPA defaults
		const currentBpa = bpaDefaultsByYear.get(currentTaxYearForClaims);
		const previousBpa = bpaDefaultsByYear.get(previousTaxYear);

		const newClaimsMap = new Map<number, EmployeeTaxClaim>();

		// Current year placeholder
		newClaimsMap.set(currentTaxYearForClaims, {
			id: '',
			employeeId: '',
			companyId: '',
			taxYear: currentTaxYearForClaims,
			federalBpa: currentBpa?.federalBPA ?? FEDERAL_BPA_2025,
			federalAdditionalClaims: federalAdditionalClaims,
			federalTotalClaim: (currentBpa?.federalBPA ?? FEDERAL_BPA_2025) + federalAdditionalClaims,
			provincialBpa: currentBpa?.provincialBPA ?? PROVINCIAL_BPA_2025[province],
			provincialAdditionalClaims: provincialAdditionalClaims,
			provincialTotalClaim: (currentBpa?.provincialBPA ?? PROVINCIAL_BPA_2025[province]) + provincialAdditionalClaims,
			createdAt: '',
			updatedAt: ''
		});

		// Previous year placeholder
		newClaimsMap.set(previousTaxYear, {
			id: '',
			employeeId: '',
			companyId: '',
			taxYear: previousTaxYear,
			federalBpa: previousBpa?.federalBPA ?? FEDERAL_BPA_2025,
			federalAdditionalClaims: 0,
			federalTotalClaim: previousBpa?.federalBPA ?? FEDERAL_BPA_2025,
			provincialBpa: previousBpa?.provincialBPA ?? PROVINCIAL_BPA_2025[province],
			provincialAdditionalClaims: 0,
			provincialTotalClaim: previousBpa?.provincialBPA ?? PROVINCIAL_BPA_2025[province],
			createdAt: '',
			updatedAt: ''
		});

		taxClaimsByYear = newClaimsMap;
	}

	/**
	 * Load BPA defaults for both tax years
	 */
	async function loadBpaDefaultsForYears(prov: Province) {
		try {
			const [currentBpa, previousBpa] = await Promise.all([
				getBPADefaultsByYear(prov, currentTaxYearForClaims),
				getBPADefaultsByYear(prov, previousTaxYear)
			]);

			const bpaMap = new Map<number, BPADefaults>();
			bpaMap.set(currentTaxYearForClaims, currentBpa);
			bpaMap.set(previousTaxYear, previousBpa);
			bpaDefaultsByYear = bpaMap;

			// Sync new BPA values to taxClaimsByYear (Fix: BPA not refreshed on province change)
			syncBpaToTaxClaims(bpaMap);
		} catch (err) {
			console.error('Failed to load BPA defaults:', err);
		}
	}

	/**
	 * Sync BPA defaults to taxClaimsByYear.
	 * Called when province changes to update BPA values in existing claims.
	 */
	function syncBpaToTaxClaims(bpaMap: Map<number, BPADefaults>) {
		if (taxClaimsByYear.size === 0) return;

		const updatedClaims = new Map<number, EmployeeTaxClaim>();

		for (const [year, claim] of taxClaimsByYear) {
			const bpaForYear = bpaMap.get(year);
			if (bpaForYear) {
				updatedClaims.set(year, {
					...claim,
					federalBpa: bpaForYear.federalBPA,
					provincialBpa: bpaForYear.provincialBPA,
					federalTotalClaim: bpaForYear.federalBPA + claim.federalAdditionalClaims,
					provincialTotalClaim: bpaForYear.provincialBPA + claim.provincialAdditionalClaims
				});
			} else {
				updatedClaims.set(year, claim);
			}
		}

		taxClaimsByYear = updatedClaims;
	}

	/**
	 * Handle claim update from TaxYearClaimsCard
	 */
	function handleClaimUpdate(year: number, fedAdditional: number, provAdditional: number) {
		const existingClaim = taxClaimsByYear.get(year);
		const bpaForYear = bpaDefaultsByYear.get(year);

		const updatedClaim: EmployeeTaxClaim = {
			id: existingClaim?.id ?? '',
			employeeId: existingClaim?.employeeId ?? employee?.id ?? '',
			companyId: existingClaim?.companyId ?? '',
			taxYear: year,
			federalBpa: existingClaim?.federalBpa ?? bpaForYear?.federalBPA ?? FEDERAL_BPA_2025,
			federalAdditionalClaims: fedAdditional,
			federalTotalClaim: (existingClaim?.federalBpa ?? bpaForYear?.federalBPA ?? FEDERAL_BPA_2025) + fedAdditional,
			provincialBpa: existingClaim?.provincialBpa ?? bpaForYear?.provincialBPA ?? PROVINCIAL_BPA_2025[province],
			provincialAdditionalClaims: provAdditional,
			provincialTotalClaim: (existingClaim?.provincialBpa ?? bpaForYear?.provincialBPA ?? PROVINCIAL_BPA_2025[province]) + provAdditional,
			createdAt: existingClaim?.createdAt ?? '',
			updatedAt: existingClaim?.updatedAt ?? ''
		};

		// Create a new Map to trigger reactivity
		const newMap = new Map(taxClaimsByYear);
		newMap.set(year, updatedClaim);
		taxClaimsByYear = newMap;

		// Sync legacy state if updating current year
		if (year === currentTaxYearForClaims) {
			federalAdditionalClaims = fedAdditional;
			provincialAdditionalClaims = provAdditional;
		}
	}


	// Prior Employment (for transferred employees - CPP/EI only)
	// Contribution limits - fetched from API with fallback to 2025 values
	let contributionLimits = $state<ContributionLimits | null>(null);
	let limitsLoading = $state(false);

	// Fallback values (2025) - used while loading or if API fails
	const FALLBACK_MAX_CPP = 4034.10;
	const FALLBACK_MAX_CPP2 = 396.00;
	const FALLBACK_MAX_EI = 1077.48;
	const HIGH_INCOME_THRESHOLD = 65000;

	// Derived: Current max values (from API or fallback)
	const maxCpp = $derived(contributionLimits?.cpp.maxBaseContribution ?? FALLBACK_MAX_CPP);
	const maxCpp2 = $derived(contributionLimits?.cpp.maxAdditionalContribution ?? FALLBACK_MAX_CPP2);
	const maxEi = $derived(contributionLimits?.ei.maxEmployeePremium ?? FALLBACK_MAX_EI);

	// Fetch contribution limits on component init
	$effect(() => {
		limitsLoading = true;
		getContributionLimits().then(limits => {
			contributionLimits = limits;
			limitsLoading = false;
		}).catch(() => {
			// Fallback values are already set via $derived
			limitsLoading = false;
		});
	});

	let hasPriorEmployment = $state(
		(employee?.initialYtdCpp ?? 0) > 0 ||
		(employee?.initialYtdCpp2 ?? 0) > 0 ||
		(employee?.initialYtdEi ?? 0) > 0
	);
	let incomeLevel = $state<'low' | 'high'>(
		hasPriorEmployment ? 'high' : 'low'
	);
	let initialYtdCpp = $state(employee?.initialYtdCpp ?? 0);
	let initialYtdCpp2 = $state(employee?.initialYtdCpp2 ?? 0);
	let initialYtdEi = $state(employee?.initialYtdEi ?? 0);
	// Track which tax year the initial YTD values apply to (auto-set to current year when values entered)
	const currentTaxYear = new Date().getFullYear();
	let initialYtdYear = $state<number | null>(employee?.initialYtdYear ?? null);

	// Hire Date → Prior Employment linkage
	// Determines whether to show the Prior Employment section based on hire date
	const hireDateInfo = $derived(() => {
		if (!hireDate) {
			return { showSection: false, defaultPriorEmployment: false, message: '' };
		}

		const hireDateObj = new Date(hireDate);
		const hireYear = hireDateObj.getFullYear();
		const hireMonth = hireDateObj.getMonth(); // 0-indexed
		const hireDay = hireDateObj.getDate();
		const today = new Date();

		// Future date: hide section
		if (hireDateObj > today) {
			return {
				showSection: false,
				defaultPriorEmployment: false,
				message: 'Prior employment section is hidden for future hire dates.'
			};
		}

		// Before current tax year: hide or show "Not applicable"
		if (hireYear < currentTaxYear) {
			return {
				showSection: false,
				defaultPriorEmployment: false,
				message: 'Not applicable - employee started before the current tax year.'
			};
		}

		// Current tax year: check if early year (Jan 1-15) or mid-year (Jan 16+)
		if (hireYear === currentTaxYear) {
			// January 1-15: show section, default "No"
			if (hireMonth === 0 && hireDay <= 15) {
				return {
					showSection: true,
					defaultPriorEmployment: false,
					message: ''
				};
			}
			// January 16+ or later months: show section, default "Yes"
			return {
				showSection: true,
				defaultPriorEmployment: true,
				message: `This employee started mid-year (${hireDateObj.toLocaleDateString('en-CA')}). They may have prior CPP/EI contributions from a previous employer.`
			};
		}

		// Fallback: show section
		return { showSection: true, defaultPriorEmployment: false, message: '' };
	});

	// Auto-update hasPriorEmployment when hire date changes (only for new employees)
	$effect(() => {
		const info = hireDateInfo();
		// Only auto-set for new employees (create mode) and when hire date changes
		if (mode === 'create' && info.showSection) {
			// Check if there are existing prior YTD values
			const hasExistingPriorYtd = initialYtdCpp > 0 || initialYtdCpp2 > 0 || initialYtdEi > 0;
			// Only update if no existing values
			if (!hasExistingPriorYtd) {
				hasPriorEmployment = info.defaultPriorEmployment;
			}
		}
	});

	// Track if employee has payroll records (determines if vacation balance is editable)
	// Must be defined before canEditPriorYtd which depends on it
	let hasPayrollRecords = $state(false);

	// Derived: Can edit prior YTD (only in create mode or if no payroll records)
	const canEditPriorYtd = $derived(mode === 'create' || !hasPayrollRecords);

	// Vacation
	let vacationPayoutMethod = $state<VacationPayoutMethod>(employee?.vacationConfig?.payoutMethod ?? 'accrual');
	// Track both the preset selection and custom value
	// null override means use provincial minimum, treat as '0.04' for backward compatibility in UI
	const initialPreset = getVacationRatePreset(employee?.vacationConfig?.vacationRate ?? '0.04');
	let vacationRatePreset = $state<string>(initialPreset);
	// Custom rate as percentage (e.g., 5.77 for 5.77%)
	// Use Math.round to avoid floating point precision issues (0.0577 * 100 = 5.7700000000000005)
	let customVacationRate = $state<number>(
		initialPreset === 'custom'
			? Math.round(parseFloat(employee?.vacationConfig?.vacationRate ?? '0') * 10000) / 100
			: 4
	);
	let vacationBalance = $state(employee?.vacationBalance ?? 0);

	// Derived: actual vacation rate value (rounded to avoid floating point issues)
	const vacationRate = $derived<VacationRate>(
		vacationRatePreset === 'custom'
			? (Math.round(customVacationRate * 100) / 10000).toFixed(4)
			: vacationRatePreset
	);

	// UI state
	let isSubmitting = $state(false);
	let errors = $state<Record<string, string>>({});
	let submitError = $state<string | null>(null);

	// Derived: Years of service for vacation rate suggestion
	const yearsOfService = $derived(calculateYearsOfService(hireDate));
	const suggestedRate = $derived(suggestVacationRate(yearsOfService));

	// Province-specific vacation rates from API
	let vacationRatesConfig = $state<VacationRatesConfig | null>(null);

	// Province employment standards (vacation, sick leave, overtime, holidays)
	let provinceStandards = $state<ProvinceStandards | null>(null);
	let provinceStandardsLoading = $state(false);
	let provinceStandardsRequestVersion = 0;  // For stale response guard

	// Dynamic vacation rate options based on province
	const vacationRateOptions = $derived(() => {
		// Base options: None and Custom
		const options: { value: string; label: string }[] = [
			{ value: '0', label: 'None (Owner/Contractor)' }
		];

		// Add tiers from province config
		if (vacationRatesConfig) {
			for (const tier of vacationRatesConfig.tiers) {
				const pct = (parseFloat(tier.vacationRate) * 100).toFixed(2).replace(/\.?0+$/, '');
				const label = `${pct}% (${tier.vacationWeeks} weeks${tier.minYearsOfService > 0 ? `, ${tier.minYearsOfService}+ years` : ''})`;
				options.push({ value: tier.vacationRate, label });
			}
		} else {
			// Fallback to standard options if config not loaded
			options.push(
				{ value: '0.04', label: '4% (2 weeks)' },
				{ value: '0.06', label: '6% (3 weeks, 5+ years)' },
				{ value: '0.08', label: '8% (4 weeks, Federal 10+)' }
			);
		}

		options.push({ value: 'custom', label: 'Custom Rate' });
		return options;
	});

	// Load vacation rates when province changes
	$effect(() => {
		const currentProvince = province;
		getVacationRates(currentProvince).then(config => {
			vacationRatesConfig = config;
		}).catch(err => {
			console.warn('Failed to load vacation rates config:', err);
			vacationRatesConfig = null;
		});
	});

	// Load province employment standards when province changes
	$effect(() => {
		const currentProvince = province;
		provinceStandardsLoading = true;
		// Use untrack to avoid creating a dependency on provinceStandardsRequestVersion
		const requestVersion = untrack(() => ++provinceStandardsRequestVersion);
		getProvinceStandards(currentProvince).then(standards => {
			// Ignore stale responses from previous requests (race condition guard)
			if (requestVersion !== provinceStandardsRequestVersion) return;
			provinceStandards = standards;
			provinceStandardsLoading = false;
		}).catch(err => {
			if (requestVersion !== provinceStandardsRequestVersion) return;
			console.warn('Failed to load province standards:', err);
			provinceStandards = null;
			provinceStandardsLoading = false;
		});
	});

	// Check if employee has payroll records (for edit mode)
	$effect(() => {
		if (mode === 'edit' && employee?.id) {
			checkEmployeeHasPayrollRecords(employee.id).then(has => {
				hasPayrollRecords = has;
			});
		} else {
			hasPayrollRecords = false;
		}
	});

	// Reset form when employee prop changes (for edit mode)
	$effect(() => {
		if (mode === 'edit' && employee) {
			firstName = employee.firstName;
			lastName = employee.lastName;
			email = employee.email ?? '';
			// Address fields
			addressStreet = employee.addressStreet ?? '';
			addressCity = employee.addressCity ?? '';
			addressPostalCode = employee.addressPostalCode ?? '';
			occupation = employee.occupation ?? '';
			province = employee.provinceOfEmployment;
			payFrequency = employee.payFrequency;
			employmentType = employee.employmentType;
			hireDate = employee.hireDate;
			tags = employee.tags ?? [];
			compensationType = employee.hourlyRate ? 'hourly' : 'salaried';
			annualSalary = employee.annualSalary ?? 0;
			hourlyRate = employee.hourlyRate ?? 0;
			// Additional claims are now stored directly
			federalAdditionalClaims = employee.federalAdditionalClaims;
			provincialAdditionalClaims = employee.provincialAdditionalClaims;
			isCppExempt = employee.isCppExempt;
			isEiExempt = employee.isEiExempt;
			cpp2Exempt = employee.cpp2Exempt;
			vacationPayoutMethod = employee.vacationConfig?.payoutMethod ?? 'accrual';
			const resetPreset = getVacationRatePreset(employee.vacationConfig?.vacationRate ?? '0.04');
			vacationRatePreset = resetPreset;
			if (resetPreset === 'custom') {
				// Use Math.round to avoid floating point precision issues
				customVacationRate = Math.round(parseFloat(employee.vacationConfig?.vacationRate ?? '0') * 10000) / 100;
			}
			vacationBalance = employee.vacationBalance ?? 0;
			// Prior Employment fields
			hasPriorEmployment = (employee.initialYtdCpp ?? 0) > 0 ||
				(employee.initialYtdCpp2 ?? 0) > 0 ||
				(employee.initialYtdEi ?? 0) > 0;
			incomeLevel = hasPriorEmployment ? 'high' : 'low';
			initialYtdCpp = employee.initialYtdCpp ?? 0;
			initialYtdCpp2 = employee.initialYtdCpp2 ?? 0;
			initialYtdEi = employee.initialYtdEi ?? 0;
			initialYtdYear = employee.initialYtdYear ?? null;
			showProvinceChangeWarning = false;
			originalProvince = employee.provinceOfEmployment; // Reset original province (Fix #3)
			errors = {};
			submitError = null;
		}
	});

	// Mask SIN for display
	function maskSIN(sin: string): string {
		const digits = sin.replace(/\D/g, '');
		if (digits.length < 9) return sin;
		return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6, 9)}`;
	}

	// Province change handler - show warning if additional claims exist
	function handleProvinceChange(newProvince: Province) {
		province = newProvince;
		// Show warning if user has additional claims that may need review
		if (federalAdditionalClaims > 0 || provincialAdditionalClaims > 0) {
			showProvinceChangeWarning = true;
		}
		// BPA updates automatically via derived provincialClaimAmount
		// Additional claims remain unchanged - user decides if they need adjustment
	}

	// Tag management
	function addTag() {
		const trimmed = newTag.trim();
		if (trimmed && !tags.includes(trimmed)) {
			tags = [...tags, trimmed];
		}
		newTag = '';
	}

	function removeTag(tag: string) {
		tags = tags.filter(t => t !== tag);
	}

	function handleTagKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addTag();
		}
	}

	// Validation
	function isValidEmail(email: string): boolean {
		return !email || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
	}

	function isValidSIN(sin: string): boolean {
		const digits = sin.replace(/\D/g, '');
		return digits.length === 9;
	}

	function validate(): boolean {
		const newErrors: Record<string, string> = {};

		// Personal
		if (!firstName.trim()) newErrors.firstName = 'First name is required';
		if (!lastName.trim()) newErrors.lastName = 'Last name is required';
		if (email && !isValidEmail(email)) newErrors.email = 'Invalid email format';

		// SIN validation only in create mode
		if (mode === 'create') {
			if (!sin.trim()) newErrors.sin = 'SIN is required';
			else if (!isValidSIN(sin)) newErrors.sin = 'SIN must be 9 digits';
		}

		// Employment
		if (!province) newErrors.province = 'Province is required';
		if (!hireDate) newErrors.hireDate = 'Hire date is required';

		// Compensation
		if (compensationType === 'salaried' && (!annualSalary || annualSalary <= 0)) {
			newErrors.annualSalary = 'Annual salary is required';
		}
		if (compensationType === 'hourly' && (!hourlyRate || hourlyRate <= 0)) {
			newErrors.hourlyRate = 'Hourly rate is required';
		}

		// Tax - validate additional claims (must be >= 0)
		if (federalAdditionalClaims < 0) newErrors.federalAdditionalClaims = 'Invalid amount';
		if (provincialAdditionalClaims < 0) newErrors.provincialAdditionalClaims = 'Invalid amount';

		// Vacation - validate custom rate if selected
		if (vacationRatePreset === 'custom') {
			if (customVacationRate === null || customVacationRate === undefined || isNaN(customVacationRate)) {
				newErrors.customVacationRate = 'Please enter a valid percentage';
			} else if (customVacationRate < 0 || customVacationRate > 100) {
				newErrors.customVacationRate = 'Rate must be between 0 and 100';
			}
		}

		// Prior Employment - validate against annual maximums (only when fields are shown)
		if (hasPriorEmployment && incomeLevel === 'high' && canEditPriorYtd) {
			if (initialYtdCpp > maxCpp) {
				newErrors.initialYtdCpp = `Cannot exceed annual max ($${maxCpp.toLocaleString()})`;
			}
			if (initialYtdCpp2 > maxCpp2) {
				newErrors.initialYtdCpp2 = `Cannot exceed annual max ($${maxCpp2.toLocaleString()})`;
			}
			if (initialYtdEi > maxEi) {
				newErrors.initialYtdEi = `Cannot exceed annual max ($${maxEi.toLocaleString()})`;
			}
		}

		errors = newErrors;
		return Object.keys(newErrors).length === 0;
	}

	// Submit handler
	async function handleSubmit() {
		if (!validate()) return;

		isSubmitting = true;
		submitError = null;

		if (mode === 'create') {
			// Create new employee
			const createInput: EmployeeCreateInput = {
				first_name: firstName.trim(),
				last_name: lastName.trim(),
				sin: sin.replace(/\D/g, ''), // Strip non-digits
				email: email.trim() || null,
				province_of_employment: province,
				pay_frequency: payFrequency,
				employment_type: employmentType,
				hire_date: hireDate,
				// Address fields
				address_street: addressStreet.trim() || null,
				address_city: addressCity.trim() || null,
				address_postal_code: addressPostalCode.trim() || null,
				occupation: occupation.trim() || null,
				// Compensation
				annual_salary: compensationType === 'salaried' ? annualSalary : null,
				hourly_rate: compensationType === 'hourly' ? hourlyRate : null,
				// Legacy fields - still needed for backward compatibility
				federal_additional_claims: federalAdditionalClaims,
				provincial_additional_claims: provincialAdditionalClaims,
				is_cpp_exempt: isCppExempt,
				is_ei_exempt: isEiExempt,
				cpp2_exempt: cpp2Exempt,
				vacation_config: {
					payout_method: vacationPayoutMethod,
					vacation_rate: vacationRate
				},
				vacation_balance: vacationBalance,
				// Initial YTD for transferred employees (only include if high income)
				// Always set year when providing YTD values
				initial_ytd_cpp: hasPriorEmployment && incomeLevel === 'high' ? initialYtdCpp : 0,
				initial_ytd_cpp2: hasPriorEmployment && incomeLevel === 'high' ? initialYtdCpp2 : 0,
				initial_ytd_ei: hasPriorEmployment && incomeLevel === 'high' ? initialYtdEi : 0,
				initial_ytd_year: hasPriorEmployment && incomeLevel === 'high' ? currentTaxYear : null
			};

			const result = await createEmployee(createInput);

			if (result.error) {
				isSubmitting = false;
				submitError = result.error;
				return;
			}

			if (result.data) {
				// Create tax claims for each year
				const employeeId = result.data.id;
				const taxClaimError = await saveTaxClaimsForEmployee(employeeId);

				if (taxClaimError) {
					// Employee was created but tax claims failed - warn user but still succeed
					console.warn('Tax claim save warning:', taxClaimError);
					// Note: We still call onSuccess since the employee was created
					// The tax claims can be fixed later by editing the employee
				}

				isSubmitting = false;
				onSuccess(result.data);
			}
		} else {
			// Update existing employee
			if (!employee) return;

			const updateInput: EmployeeUpdateInput = {
				first_name: firstName.trim(),
				last_name: lastName.trim(),
				email: email.trim() || null,
				province_of_employment: province,
				pay_frequency: payFrequency,
				employment_type: employmentType,
				hire_date: hireDate,
				// Address fields
				address_street: addressStreet.trim() || null,
				address_city: addressCity.trim() || null,
				address_postal_code: addressPostalCode.trim() || null,
				occupation: occupation.trim() || null,
				// Compensation
				annual_salary: compensationType === 'salaried' ? annualSalary : null,
				hourly_rate: compensationType === 'hourly' ? hourlyRate : null,
				// Legacy fields - still needed for backward compatibility
				federal_additional_claims: federalAdditionalClaims,
				provincial_additional_claims: provincialAdditionalClaims,
				is_cpp_exempt: isCppExempt,
				is_ei_exempt: isEiExempt,
				cpp2_exempt: cpp2Exempt,
				vacation_config: {
					payout_method: vacationPayoutMethod,
					vacation_rate: vacationRate
				},
				// Only include vacation_balance if employee has no payroll records
				// Once payroll runs exist, the balance is managed by the payroll system
				...(vacationPayoutMethod === 'accrual' && !hasPayrollRecords ? { vacation_balance: vacationBalance } : {}),
				// Initial YTD for transferred employees (only editable before first payroll)
				// IMPORTANT: Always send these fields when editable to properly clear values
				// when user switches to "No prior employment" or "low income"
				// Preserve existing initialYtdYear to avoid re-dating old values when editing
				...(canEditPriorYtd ? {
					initial_ytd_cpp: hasPriorEmployment && incomeLevel === 'high' ? initialYtdCpp : 0,
					initial_ytd_cpp2: hasPriorEmployment && incomeLevel === 'high' ? initialYtdCpp2 : 0,
					initial_ytd_ei: hasPriorEmployment && incomeLevel === 'high' ? initialYtdEi : 0,
					initial_ytd_year: hasPriorEmployment && incomeLevel === 'high' ? (initialYtdYear ?? currentTaxYear) : null
				} : {})
			};

			const result = await updateEmployee(employee.id, updateInput);

			if (result.error) {
				isSubmitting = false;
				submitError = result.error;
				return;
			}

			if (result.data) {
				// Save tax claims for each year
				const taxClaimError = await saveTaxClaimsForEmployee(employee.id);

				if (taxClaimError) {
					// Employee was updated but tax claims failed - warn user but still succeed
					console.warn('Tax claim save warning:', taxClaimError);
					// Note: We still call onSuccess since the employee was updated
					// The tax claims can be fixed later by re-editing the employee
				}

				isSubmitting = false;
				onSuccess(result.data);
			}
		}
	}

	/**
	 * Save tax claims for all years to the database via backend API.
	 * Creates new claims or updates existing ones.
	 * BPA values are derived server-side from tax configuration.
	 * If province changed (Fix #3), requests BPA recalculation for existing claims.
	 * Returns an error message if any operation fails, null on success.
	 */
	async function saveTaxClaimsForEmployee(employeeId: string): Promise<string | null> {
		const years = [currentTaxYearForClaims, previousTaxYear];
		const errors: string[] = [];
		// Recalculate BPA if province changed (Fix #3)
		const shouldRecalculateBpa = provinceChanged;

		for (const year of years) {
			const claim = taxClaimsByYear.get(year);
			if (!claim) continue;

			if (claim.id) {
				// Update existing claim via API
				// If province changed, also recalculate BPA values
				const result = await updateEmployeeTaxClaimViaApi(
					employeeId,
					year,
					{
						federalAdditionalClaims: claim.federalAdditionalClaims,
						provincialAdditionalClaims: claim.provincialAdditionalClaims
					},
					shouldRecalculateBpa
				);
				if (result.error) {
					errors.push(`Failed to update ${year} tax claim: ${result.error}`);
				}
			} else {
				// Create new claim via API (BPA derived server-side)
				const result = await createEmployeeTaxClaimViaApi(
					employeeId,
					year,
					claim.federalAdditionalClaims,
					claim.provincialAdditionalClaims
				);
				if (result.error) {
					errors.push(`Failed to create ${year} tax claim: ${result.error}`);
				}
			}
		}

		return errors.length > 0 ? errors.join('; ') : null;
	}

	// Format currency for display
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			maximumFractionDigits: 0
		}).format(amount);
	}
</script>

<form class="employee-form flex flex-col gap-6" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
	{#if submitError}
		<div class="flex items-center gap-3 p-4 bg-error-50 border border-error-200 rounded-lg text-error-700">
			<i class="fas fa-exclamation-circle"></i>
			<span class="flex-1">{submitError}</span>
			<button type="button" class="bg-transparent border-none text-error-500 cursor-pointer p-1 opacity-70 hover:opacity-100" onclick={() => submitError = null}>
				<i class="fas fa-times"></i>
			</button>
		</div>
	{/if}

	<!-- Section 1: Personal Information -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Personal Information</h3>
		<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
			<div class="flex flex-col gap-2">
				<label for="firstName" class="text-body-small font-medium text-surface-700">First Name *</label>
				<input
					id="firstName"
					type="text"
					class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.firstName ? 'border-error-500' : 'border-surface-300'}"
					bind:value={firstName}
				/>
				{#if errors.firstName}
					<span class="text-auxiliary-text text-error-600">{errors.firstName}</span>
				{/if}
			</div>

			<div class="flex flex-col gap-2">
				<label for="lastName" class="text-body-small font-medium text-surface-700">Last Name *</label>
				<input
					id="lastName"
					type="text"
					class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.lastName ? 'border-error-500' : 'border-surface-300'}"
					bind:value={lastName}
				/>
				{#if errors.lastName}
					<span class="text-auxiliary-text text-error-600">{errors.lastName}</span>
				{/if}
			</div>

			<div class="flex flex-col gap-2">
				<label for="sin" class="text-body-small font-medium text-surface-700">SIN {mode === 'create' ? '*' : ''}</label>
				{#if mode === 'create'}
					<input
						id="sin"
						type="text"
						class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.sin ? 'border-error-500' : 'border-surface-300'}"
						bind:value={sin}
						placeholder="123-456-789"
						maxlength="11"
					/>
					{#if errors.sin}
						<span class="text-auxiliary-text text-error-600">{errors.sin}</span>
					{/if}
				{:else}
					<input
						id="sin"
						type="text"
						class="p-3 border border-surface-300 rounded-md text-body-content bg-surface-100 text-surface-500 cursor-not-allowed"
						value={employee?.sin ?? '***-***-***'}
						readonly
						disabled
					/>
					<span class="text-auxiliary-text text-surface-500">SIN cannot be changed after creation</span>
				{/if}
			</div>

			<div class="flex flex-col gap-2">
				<label for="email" class="text-body-small font-medium text-surface-700">Email</label>
				<input
					id="email"
					type="email"
					class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.email ? 'border-error-500' : 'border-surface-300'}"
					bind:value={email}
					placeholder="employee@company.com"
				/>
				{#if errors.email}
					<span class="text-auxiliary-text text-error-600">{errors.email}</span>
				{/if}
			</div>

			<!-- Address Fields -->
			<div class="flex flex-col gap-2 col-span-full">
				<label for="addressStreet" class="text-body-small font-medium text-surface-700">Street Address</label>
				<input
					id="addressStreet"
					type="text"
					class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
					bind:value={addressStreet}
					placeholder="e.g., 123 Main St, Unit 4"
				/>
			</div>

			<div class="flex flex-col gap-2">
				<label for="addressCity" class="text-body-small font-medium text-surface-700">City</label>
				<input
					id="addressCity"
					type="text"
					class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
					bind:value={addressCity}
					placeholder="e.g., Toronto"
				/>
			</div>

			<div class="flex flex-col gap-2">
				<label for="addressPostalCode" class="text-body-small font-medium text-surface-700">Postal Code</label>
				<input
					id="addressPostalCode"
					type="text"
					class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
					bind:value={addressPostalCode}
					placeholder="e.g., M5V 1A1"
					maxlength="7"
				/>
			</div>
		</div>
	</section>

	<!-- Section 2: Employment Details -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Employment Details</h3>
		<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
			<div class="flex flex-col gap-2">
				<label for="province" class="text-body-small font-medium text-surface-700">Province of Employment *</label>
				<select
					id="province"
					class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.province ? 'border-error-500' : 'border-surface-300'}"
					value={province}
					onchange={(e) => handleProvinceChange(e.currentTarget.value as Province)}
				>
					{#each Object.entries(PROVINCE_LABELS) as [code, label]}
						<option value={code}>{label}</option>
					{/each}
				</select>
				{#if errors.province}
					<span class="text-auxiliary-text text-error-600">{errors.province}</span>
				{/if}
			</div>

			<!-- Province Employment Standards Info Card -->
			{#if provinceStandardsLoading}
				<div class="col-span-full p-4 bg-surface-50 border border-surface-200 rounded-lg">
					<div class="flex items-center gap-2 text-surface-500 text-body-small">
						<i class="fas fa-spinner fa-spin"></i>
						<span>Loading employment standards...</span>
					</div>
				</div>
			{:else if provinceStandards}
				<div class="col-span-full p-4 bg-primary-50 border border-primary-200 rounded-lg">
					<div class="flex items-center gap-2 mb-3">
						<i class="fas fa-info-circle text-primary-500"></i>
						<h4 class="text-body-small font-semibold text-primary-700 m-0">{provinceStandards.provinceName} Employment Standards</h4>
					</div>
					<div class="grid grid-cols-4 gap-4 max-sm:grid-cols-2">
						<!-- Vacation -->
						<div class="flex flex-col gap-1">
							<span class="text-auxiliary-text text-primary-600 font-medium uppercase tracking-wide">Vacation</span>
							<span class="text-body-small text-primary-700">
								{provinceStandards.vacation.minimumWeeks} weeks ({provinceStandards.vacation.rateDisplay})
							</span>
							{#if provinceStandards.vacation.upgradeYears}
								<span class="text-auxiliary-text text-primary-500">
									{provinceStandards.vacation.upgradeWeeks} weeks after {provinceStandards.vacation.upgradeYears} years
								</span>
							{/if}
						</div>

						<!-- Sick Leave -->
						<div class="flex flex-col gap-1">
							<span class="text-auxiliary-text text-primary-600 font-medium uppercase tracking-wide">Sick Leave</span>
							{#if provinceStandards.sickLeave.paidDays > 0 || provinceStandards.sickLeave.unpaidDays > 0}
								<span class="text-body-small text-primary-700">
									{#if provinceStandards.sickLeave.paidDays > 0}
										{provinceStandards.sickLeave.paidDays} paid
									{/if}
									{#if provinceStandards.sickLeave.paidDays > 0 && provinceStandards.sickLeave.unpaidDays > 0}
										+
									{/if}
									{#if provinceStandards.sickLeave.unpaidDays > 0}
										{provinceStandards.sickLeave.unpaidDays} unpaid
									{/if}
									days/year
								</span>
								{#if provinceStandards.sickLeave.waitingPeriodDays > 0}
									<span class="text-auxiliary-text text-primary-500">
										After {provinceStandards.sickLeave.waitingPeriodDays} days
									</span>
								{/if}
							{:else}
								<span class="text-body-small text-primary-500 italic">No statutory sick leave</span>
							{/if}
						</div>

						<!-- Overtime -->
						<div class="flex flex-col gap-1">
							<span class="text-auxiliary-text text-primary-600 font-medium uppercase tracking-wide">Overtime</span>
							<span class="text-body-small text-primary-700">
								{#if provinceStandards.overtime.dailyThreshold}
									After {provinceStandards.overtime.dailyThreshold} hrs/day
								{:else}
									After {provinceStandards.overtime.weeklyThreshold} hrs/week
								{/if}
							</span>
							<span class="text-auxiliary-text text-primary-500">
								{provinceStandards.overtime.overtimeRate}x rate
								{#if provinceStandards.overtime.doubleTimeDaily}
									(2x after {provinceStandards.overtime.doubleTimeDaily} hrs)
								{/if}
							</span>
						</div>

						<!-- Statutory Holidays -->
						<div class="flex flex-col gap-1">
							<span class="text-auxiliary-text text-primary-600 font-medium uppercase tracking-wide">Stat Holidays</span>
							<span class="text-body-small text-primary-700">
								{provinceStandards.statutoryHolidaysCount} per year
							</span>
						</div>
					</div>
				</div>
			{/if}

			<div class="flex flex-col gap-2">
				<label for="payFrequency" class="text-body-small font-medium text-surface-700">Pay Frequency *</label>
				<select
					id="payFrequency"
					class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
					bind:value={payFrequency}
				>
					{#each Object.entries(PAY_FREQUENCY_LABELS) as [code, label]}
						<option value={code}>{label}</option>
					{/each}
				</select>
			</div>

			<div class="flex flex-col gap-2">
				<label for="employmentType" class="text-body-small font-medium text-surface-700">Employment Type *</label>
				<select
					id="employmentType"
					class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
					bind:value={employmentType}
				>
					{#each Object.entries(EMPLOYMENT_TYPE_LABELS) as [code, label]}
						<option value={code}>{label}</option>
					{/each}
				</select>
			</div>

			<div class="flex flex-col gap-2">
				<label for="hireDate" class="text-body-small font-medium text-surface-700">Hire Date *</label>
				<input
					id="hireDate"
					type="date"
					class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.hireDate ? 'border-error-500' : 'border-surface-300'}"
					bind:value={hireDate}
				/>
				{#if errors.hireDate}
					<span class="text-auxiliary-text text-error-600">{errors.hireDate}</span>
				{/if}
				{#if hireDate}
					<span class="text-auxiliary-text text-surface-500">Years of service: {yearsOfService.toFixed(1)} years</span>
				{/if}
			</div>

			<div class="flex flex-col gap-2">
				<label for="occupation" class="text-body-small font-medium text-surface-700">Job Title / Occupation</label>
				<input
					id="occupation"
					type="text"
					class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
					bind:value={occupation}
					placeholder="e.g., Software Developer"
				/>
			</div>

			<div class="flex flex-col gap-2 col-span-full">
				<label for="tags" class="text-body-small font-medium text-surface-700">Tags</label>
				<div class="flex flex-col gap-2">
					<div class="flex flex-wrap gap-2">
						{#each tags as tag}
							<span class="inline-flex items-center gap-1 py-1 px-3 bg-primary-100 text-primary-700 rounded-full text-body-small">
								{tag}
								<button type="button" class="flex items-center justify-center w-4 h-4 p-0 border-none bg-transparent text-primary-500 cursor-pointer rounded-full hover:bg-primary-200 hover:text-primary-700" onclick={() => removeTag(tag)}>
									<i class="fas fa-times text-xs"></i>
								</button>
							</span>
						{/each}
					</div>
					<div class="flex gap-2">
						<input
							id="tags"
							type="text"
							class="flex-1 p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
							bind:value={newTag}
							onkeydown={handleTagKeydown}
							placeholder="Add a tag..."
						/>
						<button type="button" class="py-2 px-4 border border-surface-300 rounded-md bg-white text-surface-700 text-body-small cursor-pointer transition-[150ms] hover:bg-surface-100 hover:border-surface-400 disabled:opacity-50 disabled:cursor-not-allowed" onclick={addTag} disabled={!newTag.trim()}>
							Add
						</button>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- Section 3: Compensation -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Compensation</h3>
		<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
			<div class="flex flex-col gap-2 col-span-full">
				<label class="text-body-small font-medium text-surface-700">Compensation Type *</label>
				<div class="flex gap-6 flex-wrap max-sm:flex-col max-sm:gap-3">
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input
							type="radio"
							name="compensationType"
							value="salaried"
							bind:group={compensationType}
						/>
						<span>Annual Salary</span>
					</label>
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input
							type="radio"
							name="compensationType"
							value="hourly"
							bind:group={compensationType}
						/>
						<span>Hourly Rate</span>
					</label>
				</div>
			</div>

			{#if compensationType === 'salaried'}
				<div class="flex flex-col gap-2">
					<label for="annualSalary" class="text-body-small font-medium text-surface-700">Annual Salary *</label>
					<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
						<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
						<input
							id="annualSalary"
							type="number"
							class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
							bind:value={annualSalary}
							min="0"
							step="100"
						/>
					</div>
					{#if errors.annualSalary}
						<span class="text-auxiliary-text text-error-600">{errors.annualSalary}</span>
					{/if}
				</div>
			{:else}
				<div class="flex flex-col gap-2">
					<label for="hourlyRate" class="text-body-small font-medium text-surface-700">Hourly Rate *</label>
					<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
						<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
						<input
							id="hourlyRate"
							type="number"
							class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
							bind:value={hourlyRate}
							min="0"
							step="0.01"
						/>
						<span class="p-3 bg-surface-100 text-surface-500 text-body-content">/hr</span>
					</div>
					{#if errors.hourlyRate}
						<span class="text-auxiliary-text text-error-600">{errors.hourlyRate}</span>
					{/if}
				</div>
			{/if}
		</div>
	</section>

	<!-- Section 4: Tax Information -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Tax Information (TD1)</h3>
		<p class="text-body-small text-surface-500 m-0 mb-4 flex items-center gap-2">
			<i class="fas fa-info-circle text-primary-500"></i>
			Enter additional claims from TD1 forms (spouse, dependants, etc.) for each tax year.
		</p>

		{#if showProvinceChangeWarning}
			<div class="flex items-center gap-3 p-3 mb-4 bg-warning-50 border border-warning-200 rounded-lg text-warning-700 text-body-small">
				<i class="fas fa-exclamation-triangle text-warning-500"></i>
				<span>Province changed. Please review your additional TD1 claims for all years before saving.</span>
				<button type="button" class="ml-auto bg-transparent border-none text-warning-500 cursor-pointer p-1 opacity-70 hover:opacity-100" onclick={() => showProvinceChangeWarning = false}>
					<i class="fas fa-times"></i>
				</button>
			</div>
		{/if}

		{#if taxClaimsLoading}
			<div class="flex items-center justify-center p-8 text-surface-500">
				<i class="fas fa-spinner fa-spin mr-2"></i>
				<span>Loading tax claims...</span>
			</div>
		{:else}
			<!-- Multi-year Tax Claims Cards -->
			<div class="flex flex-col gap-4 mb-6">
				<!-- Current Year -->
				<TaxYearClaimsCard
					taxYear={currentTaxYearForClaims}
					claim={taxClaimsByYear.get(currentTaxYearForClaims) ?? null}
					bpaDefaults={bpaDefaultsByYear.get(currentTaxYearForClaims) ?? null}
					{province}
					isExpanded={currentYearExpanded}
					isCurrentYear={true}
					onUpdate={handleClaimUpdate}
					onToggleExpand={() => currentYearExpanded = !currentYearExpanded}
				/>

				<!-- Previous Year -->
				<TaxYearClaimsCard
					taxYear={previousTaxYear}
					claim={taxClaimsByYear.get(previousTaxYear) ?? null}
					bpaDefaults={bpaDefaultsByYear.get(previousTaxYear) ?? null}
					{province}
					isExpanded={previousYearExpanded}
					isCurrentYear={false}
					onUpdate={handleClaimUpdate}
					onToggleExpand={() => previousYearExpanded = !previousYearExpanded}
				/>
			</div>
		{/if}

		<!-- Exemptions (unchanged, employee-level) -->
		<div class="mt-6 pt-6 border-t border-surface-200">
			<div class="flex flex-col gap-2">
				<label class="text-body-small font-medium text-surface-700">Exemptions</label>
				<div class="flex gap-6 flex-wrap max-sm:flex-col max-sm:gap-3">
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input type="checkbox" bind:checked={isCppExempt} />
						<span>CPP Exempt</span>
					</label>
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input type="checkbox" bind:checked={isEiExempt} />
						<span>EI Exempt</span>
					</label>
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input type="checkbox" bind:checked={cpp2Exempt} />
						<span>CPP2 Exempt</span>
						<span class="text-surface-400 cursor-help" title="CPT30 form on file - exempt from additional CPP contributions">
							<i class="fas fa-info-circle"></i>
						</span>
					</label>
				</div>
			</div>
		</div>
	</section>

	<!-- Section 5: Prior Employment This Year -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Prior Employment This Year</h3>

		{#if hireDateInfo().showSection}
			<p class="text-body-small text-surface-500 m-0 mb-4 flex items-start gap-2">
				<i class="fas fa-info-circle text-primary-500 mt-0.5"></i>
				<span>If this employee worked for another employer earlier this year, enter their prior CPP/EI contributions to avoid over-deduction. Income tax is automatically adjusted through Cumulative Averaging.</span>
			</p>

			<!-- Mid-year hire prompt -->
			{#if hireDateInfo().message}
				<div class="flex items-start gap-3 p-3 bg-warning-50 border border-warning-200 rounded-lg text-warning-700 text-body-small mb-4">
					<i class="fas fa-calendar-alt text-warning-500 mt-0.5"></i>
					<span>{hireDateInfo().message}</span>
				</div>
			{/if}

			<div class="flex flex-col gap-4">
				<!-- Question 1: Has prior employment? -->
				<div class="flex flex-col gap-2">
					<label class="text-body-small font-medium text-surface-700">Has this employee worked for another employer this year?</label>
					{#if canEditPriorYtd}
						<div class="flex gap-6 flex-wrap max-sm:flex-col max-sm:gap-3">
							<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
								<input
									type="radio"
									name="hasPriorEmployment"
									value="no"
									checked={!hasPriorEmployment}
									onchange={() => { hasPriorEmployment = false; }}
								/>
								<span>No - Started fresh this year</span>
							</label>
							<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
								<input
									type="radio"
									name="hasPriorEmployment"
									value="yes"
									checked={hasPriorEmployment}
									onchange={() => { hasPriorEmployment = true; }}
								/>
								<span>Yes - Transferred from another employer</span>
							</label>
						</div>
					{:else}
						<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
							{hasPriorEmployment ? 'Yes - Transferred from another employer' : 'No - Started fresh this year'}
							<span class="text-auxiliary-text text-surface-400 ml-2">(locked after first payroll)</span>
						</div>
					{/if}
				</div>

				{#if hasPriorEmployment}
					<!-- Question 2: Income level -->
					<div class="flex flex-col gap-2">
						<label class="text-body-small font-medium text-surface-700">Estimated annual income level?</label>
						{#if canEditPriorYtd}
							<div class="flex gap-6 flex-wrap max-sm:flex-col max-sm:gap-3">
								<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
									<input
										type="radio"
										name="incomeLevel"
										value="low"
										checked={incomeLevel === 'low'}
										onchange={() => { incomeLevel = 'low'; }}
									/>
									<span>Below ${HIGH_INCOME_THRESHOLD.toLocaleString()}/year</span>
								</label>
								<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
									<input
										type="radio"
										name="incomeLevel"
										value="high"
										checked={incomeLevel === 'high'}
										onchange={() => { incomeLevel = 'high'; }}
									/>
									<span>${HIGH_INCOME_THRESHOLD.toLocaleString()}/year or above</span>
								</label>
							</div>
						{:else}
							<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
								{incomeLevel === 'high' ? `$${HIGH_INCOME_THRESHOLD.toLocaleString()}/year or above` : `Below $${HIGH_INCOME_THRESHOLD.toLocaleString()}/year`}
							</div>
						{/if}
					</div>

					{#if incomeLevel === 'low'}
						<!-- Low income notice -->
						<div class="flex items-center gap-3 p-3 bg-success-50 border border-success-200 rounded-lg text-success-700 text-body-small">
							<i class="fas fa-check-circle text-success-500"></i>
							<span>No prior CPP/EI input needed - employees below ${HIGH_INCOME_THRESHOLD.toLocaleString()}/year rarely hit annual maximums.</span>
						</div>
					{:else}
						<!-- High income: Show YTD input fields -->
						<div class="grid grid-cols-3 gap-4 max-sm:grid-cols-1">
							<div class="flex flex-col gap-2">
								<label for="initialYtdCpp" class="text-body-small font-medium text-surface-700">Prior CPP Contributions</label>
								{#if canEditPriorYtd}
									<div class="flex items-center border rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10 {errors.initialYtdCpp ? 'border-error-500' : 'border-surface-300'}">
										<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
										<input
											id="initialYtdCpp"
											type="number"
											class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
											bind:value={initialYtdCpp}
											min="0"
											max={maxCpp}
											step="0.01"
										/>
									</div>
									{#if errors.initialYtdCpp}
										<span class="text-auxiliary-text text-error-600">{errors.initialYtdCpp}</span>
									{:else}
										<span class="text-auxiliary-text text-surface-500">Max: ${maxCpp.toLocaleString()}</span>
									{/if}
								{:else}
									<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
										{formatCurrency(initialYtdCpp)}
									</div>
								{/if}
							</div>

							<div class="flex flex-col gap-2">
								<label for="initialYtdEi" class="text-body-small font-medium text-surface-700">Prior EI Premiums</label>
								{#if canEditPriorYtd}
									<div class="flex items-center border rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10 {errors.initialYtdEi ? 'border-error-500' : 'border-surface-300'}">
										<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
										<input
											id="initialYtdEi"
											type="number"
											class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
											bind:value={initialYtdEi}
											min="0"
											max={maxEi}
											step="0.01"
										/>
									</div>
									{#if errors.initialYtdEi}
										<span class="text-auxiliary-text text-error-600">{errors.initialYtdEi}</span>
									{:else}
										<span class="text-auxiliary-text text-surface-500">Max: ${maxEi.toLocaleString()}</span>
									{/if}
								{:else}
									<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
										{formatCurrency(initialYtdEi)}
									</div>
								{/if}
							</div>

							<div class="flex flex-col gap-2">
								<label for="initialYtdCpp2" class="text-body-small font-medium text-surface-700">
									Prior CPP2
									<span class="text-surface-400">(optional)</span>
								</label>
								{#if canEditPriorYtd}
									<div class="flex items-center border rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10 {errors.initialYtdCpp2 ? 'border-error-500' : 'border-surface-300'}">
										<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
										<input
											id="initialYtdCpp2"
											type="number"
											class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
											bind:value={initialYtdCpp2}
											min="0"
											max={maxCpp2}
											step="0.01"
										/>
									</div>
									{#if errors.initialYtdCpp2}
										<span class="text-auxiliary-text text-error-600">{errors.initialYtdCpp2}</span>
									{:else}
										<span class="text-auxiliary-text text-surface-500">For income &gt;$71,300. Max: ${maxCpp2.toLocaleString()}</span>
									{/if}
								{:else}
									<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
										{formatCurrency(initialYtdCpp2)}
									</div>
								{/if}
							</div>
						</div>

						<!-- Help text -->
						<div class="flex items-start gap-2 p-3 bg-primary-50 border border-primary-200 rounded-lg text-primary-700 text-body-small">
							<i class="fas fa-lightbulb text-primary-500 mt-0.5"></i>
							<span>These values can be found on the employee's most recent pay stub from their previous employer.</span>
						</div>
					{/if}
				{/if}
			</div>
		{:else if hireDate}
			<!-- Section hidden - show reason -->
			<div class="flex items-start gap-3 p-4 bg-surface-50 border border-surface-200 rounded-lg text-surface-600 text-body-small">
				<i class="fas fa-calendar-check text-surface-400 mt-0.5"></i>
				<span>{hireDateInfo().message || 'Not applicable for this hire date.'}</span>
			</div>
		{:else}
			<!-- No hire date entered yet -->
			<div class="flex items-start gap-3 p-4 bg-surface-50 border border-surface-200 rounded-lg text-surface-500 text-body-small">
				<i class="fas fa-calendar text-surface-400 mt-0.5"></i>
				<span>Enter a hire date to see prior employment options.</span>
			</div>
		{/if}
	</section>

	<!-- Section 6: Vacation Settings -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Vacation Settings</h3>
		<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
			<div class="flex flex-col gap-2">
				<label for="vacationRate" class="text-body-small font-medium text-surface-700">Vacation Rate</label>
				<select
					id="vacationRate"
					class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
					bind:value={vacationRatePreset}
				>
					{#each vacationRateOptions() as { value, label }}
						<option value={value}>{label}</option>
					{/each}
				</select>
				{#if vacationRatesConfig && vacationRatePreset !== '0' && vacationRatePreset !== 'custom'}
					{@const minimumRate = vacationRatesConfig.tiers[0]?.vacationRate ?? '0.04'}
					{#if parseFloat(vacationRatePreset) < parseFloat(minimumRate)}
						<span class="text-auxiliary-text text-warning-600 flex items-center gap-1">
							<i class="fas fa-exclamation-triangle"></i>
							Provincial minimum for {vacationRatesConfig.name} is {(parseFloat(minimumRate) * 100).toFixed(2).replace(/\.?0+$/, '')}%
						</span>
					{/if}
				{/if}
			</div>

			{#if vacationRatePreset === 'custom'}
				<div class="flex flex-col gap-2">
					<label for="customVacationRate" class="text-body-small font-medium text-surface-700">Custom Rate (%) *</label>
					<div class="flex items-center border rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10 {errors.customVacationRate ? 'border-error-500' : 'border-surface-300'}">
						<input
							id="customVacationRate"
							type="number"
							inputmode="decimal"
							class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
							bind:value={customVacationRate}
							min="0"
							max="100"
							step="0.01"
							placeholder="e.g., 5.77"
						/>
						<span class="p-3 bg-surface-100 text-surface-500 text-body-content">%</span>
					</div>
					{#if errors.customVacationRate}
						<span class="text-auxiliary-text text-error-600">{errors.customVacationRate}</span>
					{:else}
						<span class="text-auxiliary-text text-surface-500">Enter any percentage (e.g., 5.77 for Saskatchewan 3+ weeks)</span>
					{/if}
				</div>
			{/if}

			{#if vacationRatePreset !== '0'}
				<div class="flex flex-col gap-2">
					<label for="vacationMethod" class="text-body-small font-medium text-surface-700">Payout Method</label>
					<select
						id="vacationMethod"
						class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
						bind:value={vacationPayoutMethod}
					>
						<option value="accrual">Accrual (pay when vacation taken)</option>
						<option value="pay_as_you_go">Pay as you go (add to each paycheck)</option>
					</select>
				</div>

				{#if vacationPayoutMethod === 'accrual'}
					{@const canEditBalance = mode === 'create' || !hasPayrollRecords}
					{#if canEditBalance}
						<div class="flex flex-col gap-2">
							<label for="vacationBalance" class="text-body-small font-medium text-surface-700">
								{mode === 'create' ? 'Initial Vacation Balance' : 'Vacation Balance'}
							</label>
							<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
								<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
								<input
									id="vacationBalance"
									type="number"
									class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
									bind:value={vacationBalance}
									min="0"
									step="0.01"
								/>
							</div>
							<span class="text-auxiliary-text text-surface-500">
								{mode === 'create' ? 'Opening balance for vacation pay accrual' : 'Editable until first payroll is processed'}
							</span>
						</div>
					{:else}
						<div class="flex flex-col gap-2">
							<label class="text-body-small font-medium text-surface-700">Current Balance</label>
							<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
								{formatCurrency(employee?.vacationBalance ?? 0)}
								<span class="text-auxiliary-text text-surface-400 ml-2">(managed by payroll)</span>
							</div>
						</div>
					{/if}
				{/if}
			{/if}
		</div>
	</section>

	<!-- Form Actions - Hidden, controlled by parent page -->
	<input type="submit" hidden />
</form>

<!-- Expose submit function to parent -->
<svelte:options accessors={true} />
