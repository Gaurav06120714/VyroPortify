export interface Resume {
  id: string;
  filename: string;
  status: "pending" | "processing" | "done" | "failed";
  created_at: string;
  updated_at: string;
}

export interface Portfolio {
  id: string;
  resume_id: string;
  template_id: string;
  slug: string;
  status: "queued" | "generating" | "published" | "failed";
  is_public: boolean;
  html_url: string | null;
  views: number;
  created_at: string;
  updated_at: string;
}

export interface PortfolioStatus {
  id: string;
  status: Portfolio["status"];
  html_url: string | null;
  slug: string;
  ai_fallback?: boolean;
}

export interface UploadResumeResponse {
  resume_id: string;
  filename: string;
  message: string;
}

export interface GeneratePortfolioResponse {
  portfolio_id: string;
  job_queued: boolean;
  message: string;
}

export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface WorkExperienceInput {
  company: string;
  role: string;
  achievements: string;
}

export interface ProjectInput {
  name: string;
  description: string;
  tech: string[];
  link: string;
}

export interface BuildResumeRequest {
  personal: { name: string; title: string };
  experience_summary: { years: number | string; tech_stack: string[] };
  work_experiences: WorkExperienceInput[];
  projects: ProjectInput[];
  education: { degree: string; institution: string; year: string };
  skills: string[];
  social_links: { github: string; linkedin: string; website: string };
  career_goal: string;
}
