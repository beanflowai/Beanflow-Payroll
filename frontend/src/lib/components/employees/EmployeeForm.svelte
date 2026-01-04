<script lang="ts">
	import { untrack } from 'svelte';
	import type {
		Employee,
		Province,
		VacationPayoutMethod,
		VacationRate,
		EmployeeCreateInput,
		EmployeeUpdateInput,
		PayFrequency,
		EmploymentType,
		EmployeeTaxClaim
	} from '$lib/types/employee';
	import {
		FEDERAL_BPA_2025,
		PROVINCIAL_BPA_2025,
		calculateYearsOfService,
		getVacationRatePreset
	} from '$lib/types/employee';
	import {
		getBPADefaults,
		getBPADefaultsByYear,
		getContributionLimits,
		type BPADefaults,
		type ContributionLimits
	} from '$lib/services/taxConfigService';
	import {
		getVacationRates,
		getProvinceStandards,
		type VacationRatesConfig,
		type ProvinceStandards
	} from '$lib/services/configService';
	import {
		createEmployee,
		updateEmployee,
		checkEmployeeHasPayrollRecords,
		getEmployeeTaxClaims,
		createEmployeeTaxClaimViaApi,
		updateEmployeeTaxClaimViaApi
	} from '$lib/services/employeeService';

	// Import section components
	import {
		PersonalInfoSection,
		EmploymentDetailsSection,
		CompensationSection,
		TaxInfoSection,
		PriorEmploymentSection,
		VacationSettingsSection
	} from './employee-form';

	interface Props {
		employee?: Employee | null;
		mode: 'create' | 'edit';
		onSuccess: (employee: Employee) => void;
		onCancel: () => void;
	}

	let { employee = null, mode, onSuccess, onCancel: _onCancel }: Props = $props();

	// ============================================
	// INITIAL VALUES FROM PROPS
	// ============================================
	// Extract initial values from employee prop once at component creation.
	// This is intentional - form state should not reactively update when the prop changes.
	// The form captures a snapshot of the employee data for editing.
	const initialValues = (() => {
		const emp = employee;
		const hasPrior =
			(emp?.initialYtdCpp ?? 0) > 0 ||
			(emp?.initialYtdCpp2 ?? 0) > 0 ||
			(emp?.initialYtdEi ?? 0) > 0;
		const vacationPreset = getVacationRatePreset(emp?.vacationConfig?.vacationRate ?? '0.04');
		return {
			// Personal Information
			firstName: emp?.firstName ?? '',
			lastName: emp?.lastName ?? '',
			email: emp?.email ?? '',
			addressStreet: emp?.addressStreet ?? '',
			addressCity: emp?.addressCity ?? '',
			addressPostalCode: emp?.addressPostalCode ?? '',
			// Employment Details
			occupation: emp?.occupation ?? '',
			province: (emp?.provinceOfEmployment ?? 'ON') as Province,
			payFrequency: (emp?.payFrequency ?? 'bi_weekly') as PayFrequency,
			employmentType: (emp?.employmentType ?? 'full_time') as EmploymentType,
			hireDate: emp?.hireDate ?? '',
			tags: emp?.tags ?? [],
			// Compensation
			compensationType: (emp?.hourlyRate ? 'hourly' : 'salaried') as 'salaried' | 'hourly',
			annualSalary: emp?.annualSalary ?? 0,
			hourlyRate: emp?.hourlyRate ?? 0,
			// Tax
			federalAdditionalClaims: emp?.federalAdditionalClaims ?? 0,
			provincialAdditionalClaims: emp?.provincialAdditionalClaims ?? 0,
			isCppExempt: emp?.isCppExempt ?? false,
			isEiExempt: emp?.isEiExempt ?? false,
			cpp2Exempt: emp?.cpp2Exempt ?? false,
			// Prior Employment
			hasPriorEmployment: hasPrior,
			incomeLevel: (hasPrior ? 'high' : 'low') as 'low' | 'high',
			initialYtdCpp: emp?.initialYtdCpp ?? 0,
			initialYtdCpp2: emp?.initialYtdCpp2 ?? 0,
			initialYtdEi: emp?.initialYtdEi ?? 0,
			initialYtdYear: emp?.initialYtdYear ?? null,
			// Vacation
			vacationPayoutMethod: (emp?.vacationConfig?.payoutMethod ??
				'accrual') as VacationPayoutMethod,
			vacationRatePreset: vacationPreset,
			customVacationRate:
				vacationPreset === 'custom'
					? Math.round(parseFloat(emp?.vacationConfig?.vacationRate ?? '0') * 10000) / 100
					: 4,
			vacationBalance: emp?.vacationBalance ?? 0
		};
	})();

	// ============================================
	// STATE DECLARATIONS
	// ============================================

	// Personal Information
	let firstName = $state(initialValues.firstName);
	let lastName = $state(initialValues.lastName);
	let sin = $state(''); // Only used in create mode
	let email = $state(initialValues.email);
	let addressStreet = $state(initialValues.addressStreet);
	let addressCity = $state(initialValues.addressCity);
	let addressPostalCode = $state(initialValues.addressPostalCode);

	// Employment Details
	let occupation = $state(initialValues.occupation);
	let province = $state<Province>(initialValues.province);
	let payFrequency = $state<PayFrequency>(initialValues.payFrequency);
	let employmentType = $state<EmploymentType>(initialValues.employmentType);
	let hireDate = $state(initialValues.hireDate);
	let tags = $state<string[]>(initialValues.tags);

	// Compensation
	let compensationType = $state<'salaried' | 'hourly'>(initialValues.compensationType);
	let annualSalary = $state(initialValues.annualSalary);
	let hourlyRate = $state(initialValues.hourlyRate);

	// Tax - Multi-year TD1 claims state
	const currentTaxYearForClaims = new Date().getFullYear();
	const previousTaxYear = currentTaxYearForClaims - 1;
	let taxClaimsByYear = $state<Map<number, EmployeeTaxClaim>>(new Map());
	let taxClaimsLoading = $state(false);
	let bpaDefaultsByYear = $state<Map<number, BPADefaults>>(new Map());
	let currentYearExpanded = $state(true);
	let previousYearExpanded = $state(false);

	// Legacy single-year state (for backward compatibility during transition)
	let bpaDefaults = $state<BPADefaults | null>(null);
	let _bpaLoading = $state(false);
	const federalBPA = $derived(bpaDefaults?.federalBPA ?? FEDERAL_BPA_2025);
	const provincialBPA = $derived(bpaDefaults?.provincialBPA ?? PROVINCIAL_BPA_2025[province]);
	let federalAdditionalClaims = $state(initialValues.federalAdditionalClaims);
	let provincialAdditionalClaims = $state(initialValues.provincialAdditionalClaims);
	let bpaRequestVersion = $state(0);
	let showProvinceChangeWarning = $state(false);
	let originalProvince = $state<Province | null>(initialValues.province);
	let provinceChanged = $derived(
		mode === 'edit' && originalProvince !== null && province !== originalProvince
	);
	let isCppExempt = $state(initialValues.isCppExempt);
	let isEiExempt = $state(initialValues.isEiExempt);
	let cpp2Exempt = $state(initialValues.cpp2Exempt);
	const _federalClaimAmount = $derived(federalBPA + federalAdditionalClaims);
	const _provincialClaimAmount = $derived(provincialBPA + provincialAdditionalClaims);

	// Prior Employment
	let contributionLimits = $state<ContributionLimits | null>(null);
	let _limitsLoading = $state(false);
	const FALLBACK_MAX_CPP = 4034.1;
	const FALLBACK_MAX_CPP2 = 396.0;
	const FALLBACK_MAX_EI = 1077.48;
	const HIGH_INCOME_THRESHOLD = 65000;
	const maxCpp = $derived(contributionLimits?.cpp.maxBaseContribution ?? FALLBACK_MAX_CPP);
	const maxCpp2 = $derived(contributionLimits?.cpp.maxAdditionalContribution ?? FALLBACK_MAX_CPP2);
	const maxEi = $derived(contributionLimits?.ei.maxEmployeePremium ?? FALLBACK_MAX_EI);
	let hasPriorEmployment = $state(initialValues.hasPriorEmployment);
	let incomeLevel = $state<'low' | 'high'>(initialValues.incomeLevel);
	let initialYtdCpp = $state(initialValues.initialYtdCpp);
	let initialYtdCpp2 = $state(initialValues.initialYtdCpp2);
	let initialYtdEi = $state(initialValues.initialYtdEi);
	const currentTaxYear = new Date().getFullYear();
	let initialYtdYear = $state<number | null>(initialValues.initialYtdYear);
	let hasPayrollRecords = $state(false);
	const canEditPriorYtd = $derived(mode === 'create' || !hasPayrollRecords);

	// Vacation
	let vacationPayoutMethod = $state<VacationPayoutMethod>(initialValues.vacationPayoutMethod);
	const initialPreset = initialValues.vacationRatePreset;
	let vacationRatePreset = $state<string>(initialPreset);
	let customVacationRate = $state<number>(initialValues.customVacationRate);
	let vacationBalance = $state(initialValues.vacationBalance);
	const vacationRate = $derived<VacationRate>(
		vacationRatePreset === 'custom'
			? (Math.round(customVacationRate * 100) / 10000).toFixed(4)
			: vacationRatePreset
	);
	let vacationRatesConfig = $state<VacationRatesConfig | null>(null);
	let provinceStandards = $state<ProvinceStandards | null>(null);
	let provinceStandardsLoading = $state(false);
	let provinceStandardsRequestVersion = 0;

	// UI state
	let _isSubmitting = $state(false);
	let errors = $state<Record<string, string>>({});
	let submitError = $state<string | null>(null);

	// Derived values
	const yearsOfService = $derived(calculateYearsOfService(hireDate));

	// Hire Date Info for Prior Employment Section
	const hireDateInfo = $derived(() => {
		if (!hireDate) {
			return { showSection: false, defaultPriorEmployment: false, message: '' };
		}

		const hireDateObj = new Date(hireDate);
		const hireYear = hireDateObj.getFullYear();
		const hireMonth = hireDateObj.getMonth();
		const hireDay = hireDateObj.getDate();
		const today = new Date();

		if (hireDateObj > today) {
			return {
				showSection: false,
				defaultPriorEmployment: false,
				message: 'Prior employment section is hidden for future hire dates.'
			};
		}

		if (hireYear < currentTaxYear) {
			return {
				showSection: false,
				defaultPriorEmployment: false,
				message: 'Not applicable - employee started before the current tax year.'
			};
		}

		if (hireYear === currentTaxYear) {
			if (hireMonth === 0 && hireDay <= 15) {
				return { showSection: true, defaultPriorEmployment: false, message: '' };
			}
			return {
				showSection: true,
				defaultPriorEmployment: true,
				message: `This employee started mid-year (${hireDateObj.toLocaleDateString('en-CA')}). They may have prior CPP/EI contributions from a previous employer.`
			};
		}

		return { showSection: true, defaultPriorEmployment: false, message: '' };
	});

	// ============================================
	// EFFECTS
	// ============================================

	// Fetch BPA when province changes
	$effect(() => {
		const currentProvince = province;
		if (currentProvince) {
			_bpaLoading = true;
			const requestVersion = untrack(() => ++bpaRequestVersion);
			getBPADefaults(currentProvince)
				.then((defaults) => {
					if (requestVersion !== bpaRequestVersion) return;
					bpaDefaults = defaults;
					_bpaLoading = false;
				})
				.catch(() => {
					if (requestVersion !== bpaRequestVersion) return;
					_bpaLoading = false;
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

	// Fetch contribution limits on component init
	$effect(() => {
		_limitsLoading = true;
		getContributionLimits()
			.then((limits) => {
				contributionLimits = limits;
				_limitsLoading = false;
			})
			.catch(() => {
				_limitsLoading = false;
			});
	});

	// Auto-update hasPriorEmployment when hire date changes (only for new employees)
	$effect(() => {
		const info = hireDateInfo();
		if (mode === 'create' && info.showSection) {
			const hasExistingPriorYtd = initialYtdCpp > 0 || initialYtdCpp2 > 0 || initialYtdEi > 0;
			if (!hasExistingPriorYtd) {
				hasPriorEmployment = info.defaultPriorEmployment;
			}
		}
	});

	// Load vacation rates when province changes
	$effect(() => {
		const currentProvince = province;
		getVacationRates(currentProvince)
			.then((config) => {
				vacationRatesConfig = config;
			})
			.catch((err) => {
				console.warn('Failed to load vacation rates config:', err);
				vacationRatesConfig = null;
			});
	});

	// Load province employment standards when province changes
	$effect(() => {
		const currentProvince = province;
		provinceStandardsLoading = true;
		const requestVersion = untrack(() => ++provinceStandardsRequestVersion);
		getProvinceStandards(currentProvince)
			.then((standards) => {
				if (requestVersion !== provinceStandardsRequestVersion) return;
				provinceStandards = standards;
				provinceStandardsLoading = false;
			})
			.catch((err) => {
				if (requestVersion !== provinceStandardsRequestVersion) return;
				console.warn('Failed to load province standards:', err);
				provinceStandards = null;
				provinceStandardsLoading = false;
			});
	});

	// Check if employee has payroll records (for edit mode)
	$effect(() => {
		if (mode === 'edit' && employee?.id) {
			checkEmployeeHasPayrollRecords(employee.id).then((has) => {
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
			federalAdditionalClaims = employee.federalAdditionalClaims;
			provincialAdditionalClaims = employee.provincialAdditionalClaims;
			isCppExempt = employee.isCppExempt;
			isEiExempt = employee.isEiExempt;
			cpp2Exempt = employee.cpp2Exempt;
			vacationPayoutMethod = employee.vacationConfig?.payoutMethod ?? 'accrual';
			const resetPreset = getVacationRatePreset(employee.vacationConfig?.vacationRate ?? '0.04');
			vacationRatePreset = resetPreset;
			if (resetPreset === 'custom') {
				customVacationRate =
					Math.round(parseFloat(employee.vacationConfig?.vacationRate ?? '0') * 10000) / 100;
			}
			vacationBalance = employee.vacationBalance ?? 0;
			hasPriorEmployment =
				(employee.initialYtdCpp ?? 0) > 0 ||
				(employee.initialYtdCpp2 ?? 0) > 0 ||
				(employee.initialYtdEi ?? 0) > 0;
			incomeLevel = hasPriorEmployment ? 'high' : 'low';
			initialYtdCpp = employee.initialYtdCpp ?? 0;
			initialYtdCpp2 = employee.initialYtdCpp2 ?? 0;
			initialYtdEi = employee.initialYtdEi ?? 0;
			initialYtdYear = employee.initialYtdYear ?? null;
			showProvinceChangeWarning = false;
			originalProvince = employee.provinceOfEmployment;
			errors = {};
			submitError = null;
		}
	});

	// ============================================
	// HELPER FUNCTIONS
	// ============================================

	async function loadTaxClaims(employeeId: string) {
		taxClaimsLoading = true;
		try {
			await loadBpaDefaultsForYears(province);
			const result = await getEmployeeTaxClaims(employeeId);
			const claimsMap = new Map<number, EmployeeTaxClaim>();

			if (result.data) {
				for (const claim of result.data) {
					claimsMap.set(claim.taxYear, claim);
				}
			}

			const years = [currentTaxYearForClaims, previousTaxYear];
			for (const year of years) {
				if (!claimsMap.has(year)) {
					const bpaForYear = bpaDefaultsByYear.get(year);
					claimsMap.set(year, {
						id: '',
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

	async function initializeNewClaims() {
		await loadBpaDefaultsForYears(province);

		const currentBpa = bpaDefaultsByYear.get(currentTaxYearForClaims);
		const previousBpa = bpaDefaultsByYear.get(previousTaxYear);
		const newClaimsMap = new Map<number, EmployeeTaxClaim>();

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
			provincialTotalClaim:
				(currentBpa?.provincialBPA ?? PROVINCIAL_BPA_2025[province]) + provincialAdditionalClaims,
			createdAt: '',
			updatedAt: ''
		});

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

			syncBpaToTaxClaims(bpaMap);
		} catch (err) {
			console.error('Failed to load BPA defaults:', err);
		}
	}

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
			federalTotalClaim:
				(existingClaim?.federalBpa ?? bpaForYear?.federalBPA ?? FEDERAL_BPA_2025) + fedAdditional,
			provincialBpa:
				existingClaim?.provincialBpa ?? bpaForYear?.provincialBPA ?? PROVINCIAL_BPA_2025[province],
			provincialAdditionalClaims: provAdditional,
			provincialTotalClaim:
				(existingClaim?.provincialBpa ??
					bpaForYear?.provincialBPA ??
					PROVINCIAL_BPA_2025[province]) + provAdditional,
			createdAt: existingClaim?.createdAt ?? '',
			updatedAt: existingClaim?.updatedAt ?? ''
		};

		const newMap = new Map(taxClaimsByYear);
		newMap.set(year, updatedClaim);
		taxClaimsByYear = newMap;

		if (year === currentTaxYearForClaims) {
			federalAdditionalClaims = fedAdditional;
			provincialAdditionalClaims = provAdditional;
		}
	}

	function handleProvinceChange(newProvince: Province) {
		province = newProvince;
		if (federalAdditionalClaims > 0 || provincialAdditionalClaims > 0) {
			showProvinceChangeWarning = true;
		}
	}

	// ============================================
	// VALIDATION
	// ============================================

	function isValidEmail(email: string): boolean {
		return !email || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
	}

	function isValidSIN(sin: string): boolean {
		const digits = sin.replace(/\D/g, '');
		return digits.length === 9;
	}

	function validate(): boolean {
		const newErrors: Record<string, string> = {};

		if (!firstName.trim()) newErrors.firstName = 'First name is required';
		if (!lastName.trim()) newErrors.lastName = 'Last name is required';
		if (email && !isValidEmail(email)) newErrors.email = 'Invalid email format';

		if (mode === 'create') {
			if (!sin.trim()) newErrors.sin = 'SIN is required';
			else if (!isValidSIN(sin)) newErrors.sin = 'SIN must be 9 digits';
		}

		if (!province) newErrors.province = 'Province is required';
		if (!hireDate) newErrors.hireDate = 'Hire date is required';

		if (compensationType === 'salaried' && (!annualSalary || annualSalary <= 0)) {
			newErrors.annualSalary = 'Annual salary is required';
		}
		if (compensationType === 'hourly' && (!hourlyRate || hourlyRate <= 0)) {
			newErrors.hourlyRate = 'Hourly rate is required';
		}

		if (federalAdditionalClaims < 0) newErrors.federalAdditionalClaims = 'Invalid amount';
		if (provincialAdditionalClaims < 0) newErrors.provincialAdditionalClaims = 'Invalid amount';

		if (vacationRatePreset === 'custom') {
			if (
				customVacationRate === null ||
				customVacationRate === undefined ||
				isNaN(customVacationRate)
			) {
				newErrors.customVacationRate = 'Please enter a valid percentage';
			} else if (customVacationRate < 0 || customVacationRate > 100) {
				newErrors.customVacationRate = 'Rate must be between 0 and 100';
			}
		}

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

	// ============================================
	// SUBMIT HANDLER
	// ============================================

	async function handleSubmit() {
		if (!validate()) return;

		_isSubmitting = true;
		submitError = null;

		if (mode === 'create') {
			const createInput: EmployeeCreateInput = {
				first_name: firstName.trim(),
				last_name: lastName.trim(),
				sin: sin.replace(/\D/g, ''),
				email: email.trim() || null,
				province_of_employment: province,
				pay_frequency: payFrequency,
				employment_type: employmentType,
				hire_date: hireDate,
				address_street: addressStreet.trim() || null,
				address_city: addressCity.trim() || null,
				address_postal_code: addressPostalCode.trim() || null,
				occupation: occupation.trim() || null,
				annual_salary: compensationType === 'salaried' ? annualSalary : null,
				hourly_rate: compensationType === 'hourly' ? hourlyRate : null,
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
				initial_ytd_cpp: hasPriorEmployment && incomeLevel === 'high' ? initialYtdCpp : 0,
				initial_ytd_cpp2: hasPriorEmployment && incomeLevel === 'high' ? initialYtdCpp2 : 0,
				initial_ytd_ei: hasPriorEmployment && incomeLevel === 'high' ? initialYtdEi : 0,
				initial_ytd_year: hasPriorEmployment && incomeLevel === 'high' ? currentTaxYear : null
			};

			const result = await createEmployee(createInput);

			if (result.error) {
				_isSubmitting = false;
				submitError = result.error;
				return;
			}

			if (result.data) {
				const employeeId = result.data.id;
				const taxClaimError = await saveTaxClaimsForEmployee(employeeId);
				if (taxClaimError) {
					console.warn('Tax claim save warning:', taxClaimError);
				}
				_isSubmitting = false;
				onSuccess(result.data);
			}
		} else {
			if (!employee) return;

			const updateInput: EmployeeUpdateInput = {
				first_name: firstName.trim(),
				last_name: lastName.trim(),
				email: email.trim() || null,
				province_of_employment: province,
				pay_frequency: payFrequency,
				employment_type: employmentType,
				hire_date: hireDate,
				address_street: addressStreet.trim() || null,
				address_city: addressCity.trim() || null,
				address_postal_code: addressPostalCode.trim() || null,
				occupation: occupation.trim() || null,
				annual_salary: compensationType === 'salaried' ? annualSalary : null,
				hourly_rate: compensationType === 'hourly' ? hourlyRate : null,
				federal_additional_claims: federalAdditionalClaims,
				provincial_additional_claims: provincialAdditionalClaims,
				is_cpp_exempt: isCppExempt,
				is_ei_exempt: isEiExempt,
				cpp2_exempt: cpp2Exempt,
				vacation_config: {
					payout_method: vacationPayoutMethod,
					vacation_rate: vacationRate
				},
				...(vacationPayoutMethod === 'accrual' && !hasPayrollRecords
					? { vacation_balance: vacationBalance }
					: {}),
				...(canEditPriorYtd
					? {
							initial_ytd_cpp: hasPriorEmployment && incomeLevel === 'high' ? initialYtdCpp : 0,
							initial_ytd_cpp2: hasPriorEmployment && incomeLevel === 'high' ? initialYtdCpp2 : 0,
							initial_ytd_ei: hasPriorEmployment && incomeLevel === 'high' ? initialYtdEi : 0,
							initial_ytd_year:
								hasPriorEmployment && incomeLevel === 'high'
									? (initialYtdYear ?? currentTaxYear)
									: null
						}
					: {})
			};

			const result = await updateEmployee(employee.id, updateInput);

			if (result.error) {
				_isSubmitting = false;
				submitError = result.error;
				return;
			}

			if (result.data) {
				const taxClaimError = await saveTaxClaimsForEmployee(employee.id);
				if (taxClaimError) {
					console.warn('Tax claim save warning:', taxClaimError);
				}
				_isSubmitting = false;
				onSuccess(result.data);
			}
		}
	}

	async function saveTaxClaimsForEmployee(employeeId: string): Promise<string | null> {
		const years = [currentTaxYearForClaims, previousTaxYear];
		const claimErrors: string[] = [];
		const shouldRecalculateBpa = provinceChanged;

		for (const year of years) {
			const claim = taxClaimsByYear.get(year);
			if (!claim) continue;

			if (claim.id) {
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
					claimErrors.push(`Failed to update ${year} tax claim: ${result.error}`);
				}
			} else {
				const result = await createEmployeeTaxClaimViaApi(
					employeeId,
					year,
					claim.federalAdditionalClaims,
					claim.provincialAdditionalClaims
				);
				if (result.error) {
					claimErrors.push(`Failed to create ${year} tax claim: ${result.error}`);
				}
			}
		}

		return claimErrors.length > 0 ? claimErrors.join('; ') : null;
	}
</script>

<form
	class="employee-form flex flex-col gap-6"
	onsubmit={(e) => {
		e.preventDefault();
		handleSubmit();
	}}
>
	{#if submitError}
		<div
			class="flex items-center gap-3 p-4 bg-error-50 border border-error-200 rounded-lg text-error-700"
		>
			<i class="fas fa-exclamation-circle"></i>
			<span class="flex-1">{submitError}</span>
			<button
				type="button"
				class="bg-transparent border-none text-error-500 cursor-pointer p-1 opacity-70 hover:opacity-100"
				onclick={() => (submitError = null)}
				aria-label="Dismiss error"
			>
				<i class="fas fa-times"></i>
			</button>
		</div>
	{/if}

	<PersonalInfoSection
		{firstName}
		{lastName}
		{sin}
		{email}
		{addressStreet}
		{addressCity}
		{addressPostalCode}
		{mode}
		{employee}
		{errors}
		onFirstNameChange={(v) => (firstName = v)}
		onLastNameChange={(v) => (lastName = v)}
		onSinChange={(v) => (sin = v)}
		onEmailChange={(v) => (email = v)}
		onAddressStreetChange={(v) => (addressStreet = v)}
		onAddressCityChange={(v) => (addressCity = v)}
		onAddressPostalCodeChange={(v) => (addressPostalCode = v)}
	/>

	<EmploymentDetailsSection
		{province}
		{payFrequency}
		{employmentType}
		{hireDate}
		{occupation}
		{tags}
		{provinceStandards}
		{provinceStandardsLoading}
		{yearsOfService}
		{errors}
		onProvinceChange={handleProvinceChange}
		onPayFrequencyChange={(v) => (payFrequency = v)}
		onEmploymentTypeChange={(v) => (employmentType = v)}
		onHireDateChange={(v) => (hireDate = v)}
		onOccupationChange={(v) => (occupation = v)}
		onTagsChange={(v) => (tags = v)}
	/>

	<CompensationSection
		{compensationType}
		{annualSalary}
		{hourlyRate}
		{errors}
		onCompensationTypeChange={(v) => (compensationType = v)}
		onAnnualSalaryChange={(v) => (annualSalary = v)}
		onHourlyRateChange={(v) => (hourlyRate = v)}
	/>

	<TaxInfoSection
		{taxClaimsByYear}
		{bpaDefaultsByYear}
		{province}
		{isCppExempt}
		{isEiExempt}
		{cpp2Exempt}
		{showProvinceChangeWarning}
		{taxClaimsLoading}
		currentTaxYear={currentTaxYearForClaims}
		{previousTaxYear}
		{currentYearExpanded}
		{previousYearExpanded}
		onClaimUpdate={handleClaimUpdate}
		onCppExemptChange={(v) => (isCppExempt = v)}
		onEiExemptChange={(v) => (isEiExempt = v)}
		onCpp2ExemptChange={(v) => (cpp2Exempt = v)}
		onDismissWarning={() => (showProvinceChangeWarning = false)}
		onToggleCurrentYearExpand={() => (currentYearExpanded = !currentYearExpanded)}
		onTogglePreviousYearExpand={() => (previousYearExpanded = !previousYearExpanded)}
	/>

	<PriorEmploymentSection
		{hireDate}
		hireDateInfo={hireDateInfo()}
		{hasPriorEmployment}
		{incomeLevel}
		{initialYtdCpp}
		{initialYtdCpp2}
		{initialYtdEi}
		{canEditPriorYtd}
		{maxCpp}
		{maxCpp2}
		{maxEi}
		highIncomeThreshold={HIGH_INCOME_THRESHOLD}
		{errors}
		onHasPriorEmploymentChange={(v) => (hasPriorEmployment = v)}
		onIncomeLevelChange={(v) => (incomeLevel = v)}
		onInitialYtdCppChange={(v) => (initialYtdCpp = v)}
		onInitialYtdCpp2Change={(v) => (initialYtdCpp2 = v)}
		onInitialYtdEiChange={(v) => (initialYtdEi = v)}
	/>

	<VacationSettingsSection
		{vacationRatePreset}
		{customVacationRate}
		{vacationPayoutMethod}
		{vacationBalance}
		{vacationRatesConfig}
		{hasPayrollRecords}
		{mode}
		{employee}
		{errors}
		onVacationRatePresetChange={(v) => (vacationRatePreset = v)}
		onCustomVacationRateChange={(v) => (customVacationRate = v)}
		onVacationPayoutMethodChange={(v) => (vacationPayoutMethod = v)}
		onVacationBalanceChange={(v) => (vacationBalance = v)}
	/>

	<!-- Form Actions - Hidden, controlled by parent page -->
	<input type="submit" hidden />
</form>
