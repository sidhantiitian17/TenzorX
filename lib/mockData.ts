import type {
  ClinicalMapping,
  CostBreakdown,
  CostEstimate,
  CostRange,
  ConfidenceFactor,
  TierComparison,
  Hospital,
  LenderRiskProfile,
  PathwayStep,
  SearchData,
} from '@/types';

const DATA_SOURCES = [
  'NHA procedure benchmark categories',
  'Public hospital directories',
  'NABH accreditation registry',
  'Patient review intelligence (public sources)',
];

const ONCOLOGY_WEB_SOURCES = [
  'Balco Medical Centre official oncology information (balcomedicalcentre.com)',
  'Ramkrishna CARE Hospitals Raipur oncology information (carehospitals.com)',
  'AIIMS Raipur oncology and radiation oncology department information (aiimsraipur.edu.in)',
];

export const suggestionChips = [
  'Knee replacement near Nagpur under Rs 2 lakh',
  'Heart bypass under Rs 3 lakh',
  'Best cancer hospital in Raipur',
  'What is angioplasty?',
  'Explain my diabetes diagnosis',
];

const pathwayByProcedure: Record<string, PathwayStep[]> = {
  'Total Knee Arthroplasty (TKA)': [
    { step: 1, name: 'Pre-op assessment', duration: '1-2 days', cost_range: { min: 3000, max: 8000 } },
    { step: 2, name: 'Implant selection', duration: '1 day', cost_range: { min: 20000, max: 60000 } },
    { step: 3, name: 'Surgery', duration: '2-3 hrs', cost_range: { min: 80000, max: 120000 } },
    { step: 4, name: 'Hospital recovery', duration: '3-5 days', cost_range: { min: 30000, max: 60000 } },
    { step: 5, name: 'Physiotherapy follow-up', duration: '6-12 weeks', cost_range: { min: 5000, max: 15000 } },
  ],
  Angioplasty: [
    { step: 1, name: 'Consultation', duration: '1 day', cost_range: { min: 1000, max: 3000 } },
    { step: 2, name: 'Diagnostics', duration: '1-2 days', cost_range: { min: 5000, max: 15000 } },
    { step: 3, name: 'Procedure', duration: '1-2 hrs', cost_range: { min: 70000, max: 150000 } },
    { step: 4, name: 'Observation stay', duration: '2-3 days', cost_range: { min: 15000, max: 35000 } },
    { step: 5, name: 'Follow-up medication', duration: '4-8 weeks', cost_range: { min: 3000, max: 12000 } },
  ],
  'CABG / Bypass': [
    { step: 1, name: 'Cardiology consultation', duration: '1 day', cost_range: { min: 1500, max: 4000 } },
    { step: 2, name: 'Pre-op testing', duration: '2-3 days', cost_range: { min: 10000, max: 20000 } },
    { step: 3, name: 'Bypass surgery', duration: '4-6 hrs', cost_range: { min: 140000, max: 260000 } },
    { step: 4, name: 'ICU / ward recovery', duration: '5-8 days', cost_range: { min: 40000, max: 90000 } },
    { step: 5, name: 'Follow-up & rehab', duration: '4-8 weeks', cost_range: { min: 10000, max: 25000 } },
  ],
  'Cataract Surgery': [
    { step: 1, name: 'Eye evaluation', duration: '1 day', cost_range: { min: 800, max: 2000 } },
    { step: 2, name: 'Lens selection', duration: '1 day', cost_range: { min: 5000, max: 18000 } },
    { step: 3, name: 'Procedure', duration: '30-60 min', cost_range: { min: 20000, max: 45000 } },
    { step: 4, name: 'Recovery & drops', duration: '1-2 weeks', cost_range: { min: 2000, max: 6000 } },
  ],
  'Oncology Evaluation & Treatment Planning': [
    { step: 1, name: 'Oncology consultation', duration: '1 day', cost_range: { min: 1500, max: 5000 } },
    { step: 2, name: 'Staging diagnostics', duration: '2-4 days', cost_range: { min: 18000, max: 50000 } },
    { step: 3, name: 'Tumor board treatment planning', duration: '1-2 days', cost_range: { min: 10000, max: 30000 } },
    { step: 4, name: 'Initial treatment cycle', duration: '3-7 days', cost_range: { min: 90000, max: 220000 } },
    { step: 5, name: 'Follow-up and supportive care', duration: '2-4 weeks', cost_range: { min: 12000, max: 40000 } },
  ],
};

const confidenceFactors: ConfidenceFactor[] = [
  { key: 'data_availability', label: 'Data availability', score: 82, weight: 0.35, note: 'Broad hospital pricing coverage exists for this procedure.' },
  { key: 'pricing_consistency', label: 'Pricing consistency', score: 76, weight: 0.25, note: 'Hospital quotes show moderate spread around the benchmark.' },
  { key: 'recency', label: 'Benchmark recency', score: 71, weight: 0.2, note: 'Most benchmark inputs are recent enough for a stable estimate.' },
  { key: 'patient_complexity', label: 'Patient complexity', score: 68, weight: 0.2, note: 'Age and comorbidity modifiers can widen the range.' },
];

const tierComparisonForKnee: TierComparison = {
  budget: { min: 80000, max: 120000 },
  mid: { min: 120000, max: 220000 },
  premium: { min: 250000, max: 450000 },
};

export const medicalTerms = [
  { term: 'Angioplasty', simple_explanation: 'A procedure to open narrowed heart blood vessels.', analogy: 'Like unclogging a pipe.', related_terms: ['stent', 'cardiology'] },
  { term: 'ICU', simple_explanation: 'A special unit for close monitoring after serious procedures.', analogy: 'A high-attention recovery zone.', related_terms: ['HDU', 'critical care'] },
  { term: 'Comorbidity', simple_explanation: 'Another health condition you already have.', analogy: 'An extra factor that can change the path.', related_terms: ['diabetes', 'hypertension'] },
  { term: 'Physiotherapy', simple_explanation: 'Guided exercises that help you recover movement and strength.', analogy: 'A structured rehab routine.', related_terms: ['rehab', 'recovery'] },
];

export const appointmentChecklists = {
  'Total Knee Arthroplasty (TKA)': {
    documents: ['Aadhar card / photo ID', 'Previous X-rays / MRI', 'Medication list', 'Insurance card', 'Doctor referral letter'],
    questions: ['What implant options are available?', 'How long will physiotherapy take?', 'What is included in the package price?'],
    forms: ['Patient Registration Form', 'Medical History Declaration', 'Consent for Surgery Form'],
  },
  Angioplasty: {
    documents: ['Aadhar card / photo ID', 'ECG / angiogram reports', 'Medication list', 'Insurance card', 'Referral letter'],
    questions: ['Is a stent included?', 'Will ICU observation be needed?', 'What is the expected recovery time?'],
    forms: ['Patient Registration Form', 'Consent for Procedure Form'],
  },
  'Oncology Evaluation & Treatment Planning': {
    documents: ['Aadhar card / photo ID', 'Biopsy / pathology reports', 'PET-CT / MRI / CT scans', 'Previous treatment summaries', 'Insurance / scheme documents'],
    questions: ['What stage is the cancer and what are treatment options?', 'What is the intent of treatment and expected outcomes?', 'What side-effects should we prepare for and how are they managed?'],
    forms: ['Patient Registration Form', 'Oncology Treatment Consent', 'Chemotherapy Day-Care Consent'],
  },
};

const procedureCatalog = {
  knee: {
    procedure: 'Total Knee Arthroplasty (TKA)',
    icd10: 'M17.11',
    icd10Label: 'Primary osteoarthritis, right knee',
    snomed: '179344001',
    category: 'Orthopedic Surgery',
  },
  angioplasty: {
    procedure: 'Angioplasty',
    icd10: 'I25.10',
    icd10Label: 'Atherosclerotic heart disease',
    snomed: '418285008',
    category: 'Cardiology',
  },
  cabg: {
    procedure: 'CABG / Bypass',
    icd10: 'I25.10',
    icd10Label: 'Atherosclerotic heart disease',
    snomed: '232717009',
    category: 'Cardiac Surgery',
  },
  cataract: {
    procedure: 'Cataract Surgery',
    icd10: 'H26.9',
    icd10Label: 'Cataract, unspecified',
    snomed: '193570009',
    category: 'Ophthalmology',
  },
  cancer: {
    procedure: 'Oncology Evaluation & Treatment Planning',
    icd10: 'C80.1',
    icd10Label: 'Malignant neoplasm, unspecified',
    snomed: '363346000',
    category: 'Oncology',
  },
} as const;

const tierMultiplier: Record<Hospital['tier'], number> = {
  budget: 0.75,
  mid: 1,
  premium: 1.35,
};

const baseBreakdown: Record<string, CostBreakdown> = {
  'Total Knee Arthroplasty (TKA)': {
    procedure: { min: 80000, max: 120000 },
    doctor_fees: { min: 15000, max: 25000 },
    hospital_stay: { min: 20000, max: 40000, nights: '4-6' },
    diagnostics: { min: 8000, max: 15000 },
    medicines: { min: 5000, max: 12000 },
    contingency: { min: 10000, max: 30000 },
  },
  Angioplasty: {
    procedure: { min: 70000, max: 140000 },
    doctor_fees: { min: 20000, max: 35000 },
    hospital_stay: { min: 18000, max: 36000, nights: '2-3' },
    diagnostics: { min: 7000, max: 14000 },
    medicines: { min: 5000, max: 11000 },
    contingency: { min: 10000, max: 28000 },
  },
  'CABG / Bypass': {
    procedure: { min: 140000, max: 260000 },
    doctor_fees: { min: 30000, max: 55000 },
    hospital_stay: { min: 40000, max: 90000, nights: '5-8' },
    diagnostics: { min: 12000, max: 25000 },
    medicines: { min: 9000, max: 20000 },
    contingency: { min: 25000, max: 70000 },
  },
  'Cataract Surgery': {
    procedure: { min: 20000, max: 45000 },
    doctor_fees: { min: 8000, max: 18000 },
    hospital_stay: { min: 3000, max: 9000, nights: '0-1' },
    diagnostics: { min: 2000, max: 6000 },
    medicines: { min: 1000, max: 4000 },
    contingency: { min: 2000, max: 8000 },
  },
  'Oncology Evaluation & Treatment Planning': {
    procedure: { min: 80000, max: 150000 },
    doctor_fees: { min: 12000, max: 25000 },
    hospital_stay: { min: 15000, max: 35000, nights: '2-5' },
    diagnostics: { min: 20000, max: 45000 },
    medicines: { min: 15000, max: 50000 },
    contingency: { min: 10000, max: 30000 },
  },
};

function withMultiplier(range: CostRange, factor: number): CostRange {
  return {
    min: Math.round(range.min * factor),
    max: Math.round(range.max * factor),
  };
}

function buildTotal(breakdown: CostBreakdown): {
  min: number;
  max: number;
  typical_min: number;
  typical_max: number;
} {
  const values = Object.values(breakdown);
  const min = values.reduce((sum, c) => sum + c.min, 0);
  const max = values.reduce((sum, c) => sum + c.max, 0);
  return {
    min,
    max,
    typical_min: Math.round(min * 1.08),
    typical_max: Math.round(max * 0.88),
  };
}

function defaultQualification(specialization: string): string {
  if (specialization.toLowerCase().includes('cardio')) return 'DM Cardiology';
  if (specialization.toLowerCase().includes('ortho')) return 'MS Orthopedics';
  if (specialization.toLowerCase().includes('surgery')) return 'MCh Surgery';
  return 'MBBS, MD';
}

function buildAvailableSlots(waitDays: number): string[] {
  const now = new Date();
  const windows = ['10:00 AM', '12:30 PM', '4:00 PM'];

  return windows.map((window, index) => {
    const slotDate = new Date(now);
    slotDate.setDate(now.getDate() + Math.max(0, waitDays - 1) + index);
    const day = slotDate.toLocaleDateString('en-IN', { weekday: 'short' });
    const month = slotDate.toLocaleDateString('en-IN', { month: 'short' });
    return `${day}, ${slotDate.getDate()} ${month} - ${window}`;
  });
}

function clampConfidence(value: number): number {
  return Math.max(0.6, Math.min(0.9, Math.round(value * 100) / 100));
}

function confidenceJitterFromId(id: string): number {
  const hash = Array.from(id).reduce((sum, ch) => sum + ch.charCodeAt(0), 0);
  // Keep confidence spread subtle: -1.5 to +1.5 percentage points.
  return ((hash % 7) - 3) * 0.005;
}

function deriveHospitalConfidence(hospital: Hospital, baseConfidence: number): number {
  const ratingAdjustment = (hospital.rating - 4) * 0.02;
  const distanceAdjustment = -Math.min(hospital.distance_km, 12) * 0.002;
  const nabhAdjustment = hospital.nabh_accredited ? 0.01 : -0.005;
  const tierAdjustment =
    hospital.tier === 'premium' ? 0.008 : hospital.tier === 'budget' ? -0.006 : 0;
  const rankAdjustment = hospital.rank_score ? (hospital.rank_score - 80) * 0.0007 : 0;

  return clampConfidence(
    baseConfidence +
      ratingAdjustment +
      distanceAdjustment +
      nabhAdjustment +
      tierAdjustment +
      rankAdjustment +
      confidenceJitterFromId(hospital.id)
  );
}

export const mockHospitals: Hospital[] = [
  {
    id: 'h-abc-ortho',
    name: 'ABC Heart & Ortho Institute',
    location: 'Civil Lines, Nagpur, Maharashtra',
    city: 'Nagpur',
    distance_km: 5.2,
    rating: 4.5,
    review_count: 312,
    tier: 'mid',
    nabh_accredited: true,
    specializations: ['Orthopedics', 'Cardiology'],
    strengths: ['High Procedure Volume', 'NABH Accredited', 'In Budget'],
    risk_flags: ['Premium room upgrades', 'Extended physiotherapy if needed'],
    cost_range: { min: 140000, max: 220000 },
    doctors: [
      { id: 'd-001', name: 'Dr. Harsh Kulkarni', specialization: 'Joint Replacement', experience_years: 14, rating: 4.6, fee_min: 1200, fee_max: 2500 },
      { id: 'd-002', name: 'Dr. Nisha Jain', specialization: 'Orthopedic Surgeon', experience_years: 11, rating: 4.4, fee_min: 1000, fee_max: 2200 },
    ],
    reviews: [
      { id: 'r-001', sentiment: 'positive', excerpt: 'Staff was caring and surgery outcome was excellent.' },
      { id: 'r-002', sentiment: 'positive', excerpt: 'Cost discussion was transparent before admission.' },
    ],
    coordinates: { lat: 21.1458, lng: 79.0882 },
    rank_score: 88,
    rank_signals: {
      clinical_capability: 90,
      reputation: 84,
      accessibility: 82,
      affordability: 85,
    },
    sentiment_data: {
      positive_pct: 79,
      themes: [
        { theme: 'Surgery outcome', mentions: 102, positive_pct: 86 },
        { theme: 'Staff behavior', mentions: 86, positive_pct: 81 },
        { theme: 'Cleanliness', mentions: 74, positive_pct: 78 },
        { theme: 'Wait times', mentions: 62, positive_pct: 59 },
        { theme: 'Cost transparency', mentions: 57, positive_pct: 72 },
      ],
      sample_quotes: [
        { text: 'Recovery planning was explained very clearly to us.', sentiment: 'positive' },
        { text: 'Admission line was slower on weekdays.', sentiment: 'concern' },
      ],
    },
    procedure_volume: 'high',
    icu_available: true,
    wait_time_days: 3,
  },
  {
    id: 'h-city-ortho',
    name: 'City Ortho Care',
    location: 'Dharampeth, Nagpur, Maharashtra',
    city: 'Nagpur',
    distance_km: 3.1,
    rating: 4.1,
    review_count: 184,
    tier: 'mid',
    nabh_accredited: false,
    specializations: ['Orthopedics', 'Physiotherapy'],
    strengths: ['Nearest Option', 'Affordable Packages', 'Fast Appointments'],
    risk_flags: ['Limited ICU beds during peak season'],
    cost_range: { min: 110000, max: 190000 },
    doctors: [
      { id: 'd-003', name: 'Dr. Milind Pathak', specialization: 'Orthopedics', experience_years: 10, rating: 4.1, fee_min: 900, fee_max: 1800 },
    ],
    reviews: [
      { id: 'r-003', sentiment: 'positive', excerpt: 'Good value for money and quick diagnostics.' },
      { id: 'r-004', sentiment: 'neutral', excerpt: 'Facilities are decent but not premium.' },
    ],
    coordinates: { lat: 21.1296, lng: 79.0726 },
    rank_score: 81,
    rank_signals: {
      clinical_capability: 78,
      reputation: 76,
      accessibility: 90,
      affordability: 83,
    },
    sentiment_data: {
      positive_pct: 71,
      themes: [
        { theme: 'Surgery outcome', mentions: 61, positive_pct: 75 },
        { theme: 'Staff behavior', mentions: 48, positive_pct: 69 },
        { theme: 'Cleanliness', mentions: 45, positive_pct: 70 },
        { theme: 'Wait times', mentions: 50, positive_pct: 64 },
        { theme: 'Cost transparency', mentions: 35, positive_pct: 68 },
      ],
      sample_quotes: [
        { text: 'Doctors were practical and did not push extras.', sentiment: 'positive' },
        { text: 'Room options are basic, but care is dependable.', sentiment: 'concern' },
      ],
    },
    procedure_volume: 'medium',
    icu_available: true,
    wait_time_days: 2,
  },
  {
    id: 'h-budget-ortho',
    name: 'Budget Ortho & General',
    location: 'Sitabuldi, Nagpur, Maharashtra',
    city: 'Nagpur',
    distance_km: 8.9,
    rating: 3.8,
    review_count: 126,
    tier: 'budget',
    nabh_accredited: true,
    specializations: ['General Surgery', 'Orthopedics'],
    strengths: ['Lowest Cost', 'Quick Admission', 'Budget Packages'],
    risk_flags: ['ICU not available', 'Outsourced advanced diagnostics'],
    cost_range: { min: 80000, max: 140000 },
    doctors: [
      { id: 'd-004', name: 'Dr. Ritu Sathe', specialization: 'General Orthopedics', experience_years: 8, rating: 3.9, fee_min: 700, fee_max: 1300 },
    ],
    reviews: [
      { id: 'r-005', sentiment: 'positive', excerpt: 'Cost-effective option for families.' },
      { id: 'r-006', sentiment: 'neutral', excerpt: 'Good basic care, limited amenities.' },
    ],
    coordinates: { lat: 21.1450, lng: 79.0917 },
    rank_score: 72,
    rank_signals: {
      clinical_capability: 68,
      reputation: 70,
      accessibility: 65,
      affordability: 92,
    },
    sentiment_data: {
      positive_pct: 63,
      themes: [
        { theme: 'Surgery outcome', mentions: 36, positive_pct: 66 },
        { theme: 'Staff behavior', mentions: 31, positive_pct: 61 },
        { theme: 'Cleanliness', mentions: 28, positive_pct: 58 },
        { theme: 'Wait times', mentions: 32, positive_pct: 57 },
        { theme: 'Cost transparency', mentions: 24, positive_pct: 69 },
      ],
      sample_quotes: [
        { text: 'Affordable package made treatment possible for us.', sentiment: 'positive' },
        { text: 'Advanced imaging had to be done outside.', sentiment: 'concern' },
      ],
    },
    procedure_volume: 'low',
    icu_available: false,
    wait_time_days: 4,
  },
  {
    id: 'h-raipur-balco',
    name: 'BALCO Medical Centre',
    location: 'Atal Nagar (Nava Raipur), Chhattisgarh',
    city: 'Raipur',
    distance_km: 12.4,
    rating: 4.6,
    review_count: 198,
    tier: 'premium',
    nabh_accredited: true,
    specializations: ['Medical Oncology', 'Radiation Oncology', 'Surgical Oncology'],
    strengths: ['Dedicated cancer center', 'Radiation oncology expertise', 'Comprehensive oncology services'],
    risk_flags: ['Advanced precision therapies may increase total package cost'],
    cost_range: { min: 180000, max: 340000 },
    doctors: [
      {
        id: 'd-010',
        name: 'Dr. Priya Menon',
        specialization: 'Medical Oncology',
        experience_years: 15,
        rating: 4.7,
        fee_min: 1500,
        fee_max: 3200,
      },
    ],
    reviews: [
      { id: 'r-012', sentiment: 'positive', excerpt: 'Detailed oncology counseling and coordinated care pathway.' },
    ],
    coordinates: { lat: 21.1617, lng: 81.7861 },
    rank_score: 92,
    rank_signals: {
      clinical_capability: 94,
      reputation: 88,
      accessibility: 76,
      affordability: 72,
    },
    sentiment_data: {
      positive_pct: 81,
      themes: [
        { theme: 'Cancer care outcomes', mentions: 64, positive_pct: 84 },
        { theme: 'Doctor communication', mentions: 58, positive_pct: 82 },
        { theme: 'Radiation therapy support', mentions: 41, positive_pct: 79 },
      ],
      sample_quotes: [
        { text: 'Treatment roadmap was explained clearly, step by step.', sentiment: 'positive' },
      ],
    },
    procedure_volume: 'high',
    icu_available: true,
    wait_time_days: 4,
  },
  {
    id: 'h-raipur-care-onco',
    name: 'Ramkrishna CARE Hospitals',
    location: 'Pachpedi Naka, Raipur, Chhattisgarh',
    city: 'Raipur',
    distance_km: 6.1,
    rating: 4.4,
    review_count: 256,
    tier: 'mid',
    nabh_accredited: true,
    specializations: ['Medical Oncology', 'Hemato Oncology', 'Surgical Oncology'],
    strengths: ['Comprehensive oncology unit', 'Tumor board planning', 'Strong specialist network'],
    risk_flags: ['Complex regimens may need repeated day-care visits'],
    cost_range: { min: 150000, max: 300000 },
    doctors: [
      {
        id: 'd-011',
        name: 'Dr. Sanjay Agrawal',
        specialization: 'Hemato Oncology',
        experience_years: 13,
        rating: 4.5,
        fee_min: 1400,
        fee_max: 2800,
      },
    ],
    reviews: [
      { id: 'r-013', sentiment: 'positive', excerpt: 'Good oncology team coordination and timely diagnostics.' },
    ],
    coordinates: { lat: 21.2441, lng: 81.6332 },
    rank_score: 88,
    rank_signals: {
      clinical_capability: 89,
      reputation: 85,
      accessibility: 84,
      affordability: 78,
    },
    sentiment_data: {
      positive_pct: 76,
      themes: [
        { theme: 'Cancer treatment support', mentions: 72, positive_pct: 79 },
        { theme: 'Diagnostics and planning', mentions: 49, positive_pct: 74 },
        { theme: 'Staff behavior', mentions: 44, positive_pct: 73 },
      ],
      sample_quotes: [
        { text: 'Oncology consult and treatment plan were handled quickly.', sentiment: 'positive' },
      ],
    },
    procedure_volume: 'high',
    icu_available: true,
    wait_time_days: 3,
  },
  {
    id: 'h-raipur-1',
    name: 'Raipur Heartline Multispecialty',
    location: 'Shankar Nagar, Raipur, Chhattisgarh',
    city: 'Raipur',
    distance_km: 4.8,
    rating: 4.3,
    review_count: 246,
    tier: 'mid',
    nabh_accredited: true,
    specializations: ['Cardiology', 'Cardiac Surgery'],
    strengths: ['Cardiac team depth', 'NABH Accredited', 'Good rehabilitation'],
    risk_flags: ['Premium stent options increase cost'],
    cost_range: { min: 160000, max: 280000 },
    doctors: [{ id: 'd-005', name: 'Dr. Abhishek Rao', specialization: 'Interventional Cardiology', experience_years: 13, rating: 4.5, fee_min: 1200, fee_max: 2800 }],
    reviews: [{ id: 'r-007', sentiment: 'positive', excerpt: 'Strong post-op monitoring and counseling.' }],
    coordinates: { lat: 21.2514, lng: 81.6296 },
    rank_score: 74,
    rank_signals: {
      clinical_capability: 81,
      reputation: 77,
      accessibility: 84,
      affordability: 70,
    },
  },
  {
    id: 'h-bhopal-1',
    name: 'Bhopal Joint & Spine Center',
    location: 'MP Nagar, Bhopal, Madhya Pradesh',
    city: 'Bhopal',
    distance_km: 6.4,
    rating: 4.2,
    review_count: 194,
    tier: 'mid',
    nabh_accredited: true,
    specializations: ['Joint Replacement', 'Spine Surgery'],
    strengths: ['High procedure focus', 'Structured rehab'],
    risk_flags: ['Room upgrades can inflate package'],
    cost_range: { min: 130000, max: 210000 },
    doctors: [{ id: 'd-006', name: 'Dr. Karthik Menon', specialization: 'Joint Replacement', experience_years: 12, rating: 4.3, fee_min: 1000, fee_max: 2200 }],
    reviews: [{ id: 'r-008', sentiment: 'positive', excerpt: 'Strong physiotherapy support after surgery.' }],
    coordinates: { lat: 23.2599, lng: 77.4126 },
  },
  {
    id: 'h-indore-1',
    name: 'Indore Advanced Care',
    location: 'Vijay Nagar, Indore, Madhya Pradesh',
    city: 'Indore',
    distance_km: 7.1,
    rating: 4.4,
    review_count: 281,
    tier: 'premium',
    nabh_accredited: true,
    specializations: ['Orthopedics', 'Cardiology', 'Oncology'],
    strengths: ['Premium infra', 'Specialist availability'],
    risk_flags: ['Higher base package'],
    cost_range: { min: 210000, max: 360000 },
    doctors: [{ id: 'd-007', name: 'Dr. Varsha Sinha', specialization: 'Orthopedic Surgery', experience_years: 16, rating: 4.6, fee_min: 1800, fee_max: 3200 }],
    reviews: [{ id: 'r-009', sentiment: 'positive', excerpt: 'Excellent facilities and specialist access.' }],
    coordinates: { lat: 22.7196, lng: 75.8577 },
  },
  {
    id: 'h-surat-1',
    name: 'Surat Specialty Hospital',
    location: 'Ring Road, Surat, Gujarat',
    city: 'Surat',
    distance_km: 5.9,
    rating: 4.4,
    review_count: 208,
    tier: 'premium',
    nabh_accredited: true,
    specializations: ['Joint Replacement', 'Sports Medicine'],
    strengths: ['Robotic surgery support', 'Premium rehab'],
    risk_flags: ['Premium implants are expensive'],
    cost_range: { min: 220000, max: 380000 },
    doctors: [{ id: 'd-008', name: 'Dr. Hitesh Shah', specialization: 'Joint Replacement', experience_years: 19, rating: 4.7, fee_min: 2000, fee_max: 3500 }],
    reviews: [{ id: 'r-010', sentiment: 'positive', excerpt: 'Very smooth surgery and high-quality rehab.' }],
    coordinates: { lat: 21.1702, lng: 72.8311 },
  },
  {
    id: 'h-patna-1',
    name: 'Patna Care General',
    location: 'Boring Road, Patna, Bihar',
    city: 'Patna',
    distance_km: 9.8,
    rating: 3.9,
    review_count: 137,
    tier: 'budget',
    nabh_accredited: false,
    specializations: ['General Medicine', 'General Surgery'],
    strengths: ['Affordable rates', 'Family support services'],
    risk_flags: ['Limited specialty depth'],
    cost_range: { min: 70000, max: 130000 },
    doctors: [{ id: 'd-009', name: 'Dr. Ankita Sahay', specialization: 'General Surgery', experience_years: 9, rating: 4.0, fee_min: 700, fee_max: 1400 }],
    reviews: [{ id: 'r-011', sentiment: 'positive', excerpt: 'Budget-friendly and responsive staff.' }],
    coordinates: { lat: 25.5941, lng: 85.1376 },
  },
];

function detectProcedure(query: string): (typeof procedureCatalog)[keyof typeof procedureCatalog] {
  const q = query.toLowerCase();
  if (q.includes('knee') || q.includes('arthroplasty')) return procedureCatalog.knee;
  if (q.includes('cancer') || q.includes('oncology') || q.includes('tumor') || q.includes('chemo') || q.includes('chemotherapy')) return procedureCatalog.cancer;
  if (q.includes('bypass') || q.includes('cabg')) return procedureCatalog.cabg;
  if (q.includes('cataract')) return procedureCatalog.cataract;
  return procedureCatalog.angioplasty;
}

function isHospitalRelevantToProcedure(
  hospital: Hospital,
  procedure: (typeof procedureCatalog)[keyof typeof procedureCatalog]
): boolean {
  const haystack = [hospital.name, ...hospital.specializations, ...hospital.strengths].join(' ').toLowerCase();

  if (procedure.category === 'Oncology') {
    return ['onco', 'cancer', 'tumor', 'radiation', 'chemo', 'haemato'].some((keyword) =>
      haystack.includes(keyword)
    );
  }
  if (procedure.category === 'Orthopedic Surgery') {
    return ['ortho', 'joint', 'knee', 'arthroplasty'].some((keyword) => haystack.includes(keyword));
  }
  if (procedure.procedure === 'CABG / Bypass') {
    return ['cardiac', 'bypass', 'heart', 'cardio'].some((keyword) => haystack.includes(keyword));
  }
  if (procedure.category === 'Cardiology') {
    return ['cardio', 'heart', 'angioplasty'].some((keyword) => haystack.includes(keyword));
  }
  if (procedure.category === 'Ophthalmology') {
    return ['eye', 'ophthal', 'cataract'].some((keyword) => haystack.includes(keyword));
  }
  return true;
}

export function generateMockSearchData(query: string, location: string): SearchData {
  const procedure = detectProcedure(query);
  const base = baseBreakdown[procedure.procedure] ?? baseBreakdown.Angioplasty;
  const overallConfidence = 0.74;

  const cityHospitals = mockHospitals.filter((h) => h.city.toLowerCase() === location.toLowerCase());
  const relevantCityHospitals = cityHospitals.filter((h) => isHospitalRelevantToProcedure(h, procedure));
  const relevantGlobalHospitals = mockHospitals.filter((h) => isHospitalRelevantToProcedure(h, procedure));

  const hospitalPool =
    relevantCityHospitals.length > 0
      ? relevantCityHospitals
      : cityHospitals.length > 0
      ? cityHospitals
      : relevantGlobalHospitals.length > 0
      ? relevantGlobalHospitals
      : mockHospitals;

  const prioritizedHospitalPool = [...hospitalPool].sort((a, b) => {
    const aScore = (a.rank_score ?? 0) + a.rating * 10;
    const bScore = (b.rank_score ?? 0) + b.rating * 10;
    return bScore - aScore;
  });

  const hospitals = prioritizedHospitalPool.slice(0, 3).map((h) => ({
    ...h,
    doctors: h.doctors.map((doctor, index) => ({
      ...doctor,
      qualification: doctor.qualification ?? defaultQualification(doctor.specialization),
      wait_time_days: doctor.wait_time_days ?? Math.max(1, (h.wait_time_days ?? 3) + index),
      booking_url: doctor.booking_url ?? `https://appointments.healthnav.in/${h.id}/${doctor.id}`,
      available_slots:
        doctor.available_slots ?? buildAvailableSlots(doctor.wait_time_days ?? Math.max(1, (h.wait_time_days ?? 3) + index)),
    })),
    rank_signals: h.rank_signals ?? {
      clinical_capability: 78,
      reputation: 74,
      accessibility: 76,
      affordability: 80,
    },
    sentiment_data: h.sentiment_data ?? {
      positive_pct: 70,
      themes: [
        { theme: 'Surgery outcome', mentions: 30, positive_pct: 72 },
        { theme: 'Staff behavior', mentions: 22, positive_pct: 69 },
      ],
      sample_quotes: [{ text: 'Overall care was reliable.', sentiment: 'positive' }],
    },
    risk_flags: h.risk_flags ?? ['Complications can extend stay'],
    procedure_volume: h.procedure_volume ?? 'medium',
    icu_available: h.icu_available ?? true,
    wait_time_days: h.wait_time_days ?? 3,
    confidence: h.confidence ?? deriveHospitalConfidence(h, overallConfidence),
  }));

  const midHospital = hospitals.find((h) => h.tier === 'mid') ?? hospitals[0];
  const factor = tierMultiplier[midHospital.tier];
  const breakdown: CostBreakdown = {
    procedure: withMultiplier(base.procedure, factor),
    doctor_fees: withMultiplier(base.doctor_fees, factor),
    hospital_stay: {
      ...withMultiplier(base.hospital_stay, factor),
      nights: base.hospital_stay.nights,
    },
    diagnostics: withMultiplier(base.diagnostics, factor),
    medicines: withMultiplier(base.medicines, factor),
    contingency: withMultiplier(base.contingency, factor),
  };

  const total = buildTotal(breakdown);
  const mappingConfidence = 0.86;

  const clinicalMapping: ClinicalMapping = {
    user_query: query,
    procedure: procedure.procedure,
    icd10_code: procedure.icd10,
    icd10_label: procedure.icd10Label,
    snomed_code: procedure.snomed,
    category: procedure.category,
    pathway: pathwayByProcedure[procedure.procedure] ?? pathwayByProcedure.Angioplasty,
    confidence: mappingConfidence,
    confidence_factors: confidenceFactors,
  };

  return {
    procedure: procedure.procedure,
    icd10_code: procedure.icd10,
    icd10_label: procedure.icd10Label,
    snomed_code: procedure.snomed,
    category: procedure.category,
    query_location: location,
    cost_range: { min: total.min, max: total.max },
    confidence: overallConfidence,
    cost_breakdown: breakdown,
    comorbidity_warnings: [],
    hospitals,
    clinical_mapping: clinicalMapping,
    pathway: clinicalMapping.pathway,
    confidence_factors: confidenceFactors,
    geo_adjustment: {
      city_tier: 'tier2',
      city_name: location,
      discount_vs_metro: 0.32,
    },
    tier_comparison: tierComparisonForKnee,
    risk_adjustments: [
      {
        factor: 'diabetes',
        impact: 'Higher complication risk',
        cost_delta_min: 10000,
        cost_delta_max: 30000,
        severity: 'medium',
      },
      {
        factor: 'cardiac history',
        impact: 'Increased ICU likelihood',
        cost_delta_min: 40000,
        cost_delta_max: 150000,
        severity: 'high',
      },
    ],
    data_sources:
      procedure.category === 'Oncology'
        ? [...DATA_SOURCES, ...ONCOLOGY_WEB_SOURCES]
        : DATA_SOURCES,
  };
}

export function buildCostEstimate(searchData: SearchData): CostEstimate {
  const totalMin = searchData.cost_range.min;
  const totalMax = searchData.cost_range.max;
  return {
    procedure: searchData.procedure,
    icd10_code: searchData.icd10_code,
    location: searchData.query_location,
    tier: 'mid',
    cost_range: { min: totalMin, max: totalMax },
    typical_range: {
      min: Math.round(totalMin * 1.08),
      max: Math.round(totalMax * 0.88),
    },
    confidence: searchData.confidence,
    confidence_factors: searchData.confidence_factors,
    cost_breakdown: searchData.cost_breakdown,
    comorbidity_warnings: searchData.comorbidity_warnings,
    geo_adjustment: searchData.geo_adjustment,
    risk_adjustments: searchData.risk_adjustments,
    data_sources: searchData.data_sources,
    tier_comparison: searchData.tier_comparison,
  };
}

export function buildLenderRiskProfile(estimate: CostEstimate): LenderRiskProfile {
  const adjustmentMin = estimate.risk_adjustments?.reduce((sum, a) => sum + a.cost_delta_min, 0) ?? 30000;
  const adjustmentMax = estimate.risk_adjustments?.reduce((sum, a) => sum + a.cost_delta_max, 0) ?? 90000;
  return {
    procedure: estimate.procedure,
    icd10_code: estimate.icd10_code,
    risk_level: estimate.confidence >= 0.7 ? 'moderate' : 'high',
    base_estimate: estimate.cost_range,
    comorbidity_adjustment: { min: adjustmentMin, max: adjustmentMax },
    max_foreseeable_cost: {
      min: estimate.cost_range.min + adjustmentMin,
      max: estimate.cost_range.max + adjustmentMax,
    },
    recommended_cover: {
      min: Math.round((estimate.cost_range.min + adjustmentMin) * 0.86),
      max: Math.round((estimate.cost_range.max + adjustmentMax) * 0.8),
    },
    confidence: estimate.confidence,
    risk_factors: [
      { factor: 'Diabetes', severity: 'high', impact: 'Higher complication risk' },
      { factor: 'Cardiac History', severity: 'medium', impact: 'ICU likelihood ~15%' },
      { factor: 'Age 45', severity: 'low', impact: 'Normal healing trajectory' },
    ],
    procedure_risk: {
      mortality_risk: 'Very Low (<0.5% for elective procedures)',
      icu_probability: '12-18% (elevated by profile)',
      avg_los_days: '4-6 days',
      readmission_rate: '~6% national benchmark',
    },
    procedure_risk_detail: {
      mortality_risk: 0.5,
      icu_probability: 15,
      avg_los_days: 5,
      readmission_rate: 6,
    },
  };
}
