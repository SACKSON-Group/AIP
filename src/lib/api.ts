import axios from 'axios';

// Production API URL - PythonAnywhere
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://sackson.pythonanywhere.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email); // Backend expects email in username field
    formData.append('password', password);
    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
  register: async (email: string, password: string, full_name: string, phone?: string) => {
    const response = await api.post('/auth/register', { email, password, full_name, phone });
    return response.data;
  },
};

// Projects API
export const projectsApi = {
  list: async (params?: { sector?: string; country?: string; stage?: string }) => {
    const response = await api.get('/projects/', { params });
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get(`/projects/${id}`);
    return response.data;
  },
  create: async (project: ProjectCreate) => {
    const response = await api.post('/projects/', project);
    return response.data;
  },
};

// Investors API
export const investorsApi = {
  list: async () => {
    const response = await api.get('/investors/');
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get(`/investors/${id}`);
    return response.data;
  },
  create: async (investor: InvestorCreate) => {
    const response = await api.post('/investors/', investor);
    return response.data;
  },
  match: async (investorId: number) => {
    const response = await api.get(`/investors/${investorId}/match`);
    return response.data;
  },
};

// Verifications API
export const verificationsApi = {
  list: async () => {
    const response = await api.get('/verifications/');
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get(`/verifications/${id}`);
    return response.data;
  },
  create: async (verification: VerificationCreate) => {
    const response = await api.post('/verifications/', verification);
    return response.data;
  },
  getByProject: async (projectId: number) => {
    const response = await api.get(`/verifications/project/${projectId}`);
    return response.data;
  },
};

// Introductions API
export const introductionsApi = {
  list: async () => {
    const response = await api.get('/introductions/');
    return response.data;
  },
  create: async (introduction: IntroductionCreate) => {
    const response = await api.post('/introductions/', introduction);
    return response.data;
  },
  updateStatus: async (id: number, status: string) => {
    const response = await api.patch(`/introductions/${id}/status`, { status });
    return response.data;
  },
};

// Data Rooms API
export const dataRoomsApi = {
  list: async () => {
    const response = await api.get('/data-rooms/');
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get(`/data-rooms/${id}`);
    return response.data;
  },
  create: async (dataRoom: DataRoomCreate) => {
    const response = await api.post('/data-rooms/', dataRoom);
    return response.data;
  },
};

// Analytics API
export const analyticsApi = {
  list: async () => {
    const response = await api.get('/analytics/');
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get(`/analytics/${id}`);
    return response.data;
  },
  create: async (report: AnalyticReportCreate) => {
    const response = await api.post('/analytics/', report);
    return response.data;
  },
};

// Events API
export const eventsApi = {
  list: async () => {
    const response = await api.get('/events/');
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get(`/events/${id}`);
    return response.data;
  },
  create: async (event: EventCreate) => {
    const response = await api.post('/events/', event);
    return response.data;
  },
};

// Types
export interface ProjectCreate {
  name: string;
  sector: string;
  country: string;
  region?: string;
  gps_location?: string;
  stage: string;
  estimated_capex: number;
  funding_gap?: number;
  timeline_fid?: string;
  timeline_cod?: string;
  revenue_model: string;
  offtaker?: string;
  tariff_mechanism?: string;
  concession_length?: number;
  fx_exposure?: string;
  political_risk_mitigation?: string;
  sovereign_support?: string;
  technology?: string;
  epc_status?: string;
  land_acquisition_status?: string;
  esg_category?: string;
  permits_status?: string;
}

export interface Project extends ProjectCreate {
  id: number;
  created_at: string;
  updated_at: string;
}

export interface InvestorCreate {
  fund_name: string;
  aum?: number;
  ticket_size_min: number;
  ticket_size_max: number;
  instruments: string[];
  target_irr?: number;
  country_focus: string[];
  sector_focus: string[];
  esg_constraints?: string;
}

export interface Investor extends InvestorCreate {
  id: number;
}

export interface VerificationCreate {
  project_id: number;
  level: string;
  bankability?: {
    technical_readiness: number;
    financial_robustness: number;
    legal_clarity: number;
    esg_compliance: number;
    overall_score: number;
    risk_flags: string[];
    last_verified: string;
  };
}

export interface Verification extends VerificationCreate {
  id: number;
}

export interface IntroductionCreate {
  investor_id: number;
  project_id: number;
  message?: string;
  nda_executed?: boolean;
  sponsor_approved?: boolean;
  status?: string;
}

export interface Introduction extends IntroductionCreate {
  id: number;
}

export interface DataRoomCreate {
  project_id: number;
  nda_required?: boolean;
  access_users?: number[];
  documents?: Record<string, string>;
}

export interface DataRoom extends DataRoomCreate {
  id: number;
  created_at: string;
}

export interface AnalyticReportCreate {
  title: string;
  sector?: string;
  country?: string;
  content: string;
}

export interface AnalyticReport extends AnalyticReportCreate {
  id: number;
  created_at: string;
}

export interface EventCreate {
  name: string;
  description: string;
  event_date: string;
  type: string;
  projects_involved?: number[];
}

export interface Event extends EventCreate {
  id: number;
}

export default api;
