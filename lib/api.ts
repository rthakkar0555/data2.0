// API service layer for connecting frontend with backend
import { config } from './config';

export interface UploadResponse {
  message: string;
  files: string[];
  db_record: {
    _id: string;
    company_name: string;
    product_name: string;
    uri: string;
  };
}

export interface QueryRequest {
  query: string;
  company_name?: string;
  product_name?: string;
}

export interface QueryResponse {
  response: string;
}

export interface Company {
  companies: string[];
}

export interface Model {
  _id: string;
  company_name: string;
  product_name: string;
  filename: string;
  uri: string;
  qr_uri?: string;
}

export interface ModelsResponse {
  models: Model[];
}

export interface HealthResponse {
  status: string;
}

export interface CurrentCompanyResponse {
  company_name: string;
}

export interface UploadedFilesResponse {
  files: string[];
}

export interface DeleteResponse {
  message: string;
  mongo_deleted: number;
  product_name: string;
  product_code: string;
}

export interface ClearConversationResponse {
  message: string;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = config.API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health/');
  }

  // Upload PDF
  async uploadPdf(
    file: File,
    companyName: string,
    productName?: string,
    productCode?: string
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('company_name', companyName);
    
    if (productName) {
      formData.append('product_name', productName);
    }
    
    if (productCode) {
      formData.append('product_code', productCode);
    }

    const url = `${this.baseUrl}/upload_pdf/`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Upload failed:', error);
      throw error;
    }
  }

  // Query the system
  async query(request: QueryRequest): Promise<QueryResponse> {
    return this.request<QueryResponse>('/query/', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Get all companies
  async getCompanies(): Promise<Company> {
    return this.request<Company>('/companies/');
  }

  // Get current company
  async getCurrentCompany(): Promise<CurrentCompanyResponse> {
    return this.request<CurrentCompanyResponse>('/companies/current/');
  }

  // Get models for a company
  async getModelsForCompany(company: string): Promise<ModelsResponse> {
    return this.request<ModelsResponse>(`/companies/${encodeURIComponent(company)}/models/`);
  }

  // Get uploaded files
  async getUploadedFiles(): Promise<UploadedFilesResponse> {
    return this.request<UploadedFilesResponse>('/get_uploaded_files/');
  }

  // Remove file
  async removeFile(fileName: string): Promise<{ message: string; files: string[] }> {
    return this.request<{ message: string; files: string[] }>(`/remove_file/?file_name=${encodeURIComponent(fileName)}`, {
      method: 'POST',
    });
  }

  // Generate QR codes for existing entries
  async generateQrForExisting(): Promise<{ message: string; updated_count: number }> {
    return this.request<{ message: string; updated_count: number }>('/generate_qr_for_existing/', {
      method: 'POST',
    });
  }

  // Delete manual from both MongoDB and Qdrant DB
  async deleteManual(productName: string, productCode: string): Promise<DeleteResponse> {
    const formData = new FormData();
    formData.append('product_name', productName);
    formData.append('product_code', productCode);

    const url = `${this.baseUrl}/delete_manual/`;
    
    try {
      const response = await fetch(url, {
        method: 'DELETE',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Delete failed:', error);
      throw error;
    }
  }

  // Clear conversation memory
  async clearConversation(): Promise<ClearConversationResponse> {
    return this.request<ClearConversationResponse>('/conversation/clear/');
  }
}

// Create a singleton instance
export const apiService = new ApiService();

// Export individual methods for convenience
export const {
  healthCheck,
  uploadPdf,
  query,
  getCompanies,
  getCurrentCompany,
  getModelsForCompany,
  getUploadedFiles,
  removeFile,
  generateQrForExisting,
  deleteManual,
  clearConversation,
} = apiService;
