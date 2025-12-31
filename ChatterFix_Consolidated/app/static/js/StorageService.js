// Cloud Storage Services for RAG Document Management

class StorageService {
  constructor(config) {
    this.config = config;
    this.provider = config.provider;
  }

  async uploadFile(file, metadata = {}) {
    switch (this.provider) {
      case 'secure-db':
        return this.uploadToSecureDB(file, metadata);
      case 'google-cloud':
        return this.uploadToGCS(file, metadata);
      case 'aws-s3':
        return this.uploadToS3(file, metadata);
      case 'azure-blob':
        return this.uploadToAzure(file, metadata);
      default:
        throw new Error(`Unsupported storage provider: ${this.provider}`);
    }
  }

  async downloadFile(fileId) {
    switch (this.provider) {
      case 'secure-db':
        return this.downloadFromSecureDB(fileId);
      case 'google-cloud':
        return this.downloadFromGCS(fileId);
      case 'aws-s3':
        return this.downloadFromS3(fileId);
      case 'azure-blob':
        return this.downloadFromAzure(fileId);
      default:
        throw new Error(`Unsupported storage provider: ${this.provider}`);
    }
  }

  async deleteFile(fileId) {
    switch (this.provider) {
      case 'secure-db':
        return this.deleteFromSecureDB(fileId);
      case 'google-cloud':
        return this.deleteFromGCS(fileId);
      case 'aws-s3':
        return this.deleteFromS3(fileId);
      case 'azure-blob':
        return this.deleteFromAzure(fileId);
      default:
        throw new Error(`Unsupported storage provider: ${this.provider}`);
    }
  }

  async listFiles(prefix = '') {
    switch (this.provider) {
      case 'secure-db':
        return this.listFromSecureDB(prefix);
      case 'google-cloud':
        return this.listFromGCS(prefix);
      case 'aws-s3':
        return this.listFromS3(prefix);
      case 'azure-blob':
        return this.listFromAzure(prefix);
      default:
        throw new Error(`Unsupported storage provider: ${this.provider}`);
    }
  }

  // Secure Database Implementation (Default)
  async uploadToSecureDB(file, metadata) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));

    const response = await fetch('/api/storage/secure-db/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async downloadFromSecureDB(fileId) {
    const response = await fetch(`/api/storage/secure-db/download/${fileId}`, {
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }

    return response.blob();
  }

  async deleteFromSecureDB(fileId) {
    const response = await fetch(`/api/storage/secure-db/delete/${fileId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`Delete failed: ${response.statusText}`);
    }

    return response.json();
  }

  async listFromSecureDB(prefix) {
    const response = await fetch(`/api/storage/secure-db/list?prefix=${encodeURIComponent(prefix)}`, {
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`List failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Google Cloud Storage Implementation
  async uploadToGCS(file, metadata) {
    // Generate signed URL for upload
    const signedUrlResponse = await fetch('/api/storage/gcs/signed-url', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify({
        fileName: file.name,
        contentType: file.type,
        metadata: metadata,
        bucketName: this.config.config.bucketName
      })
    });

    if (!signedUrlResponse.ok) {
      throw new Error('Failed to get signed URL');
    }

    const { signedUrl, fileId } = await signedUrlResponse.json();

    // Upload to GCS using signed URL
    const uploadResponse = await fetch(signedUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type
      },
      body: file
    });

    if (!uploadResponse.ok) {
      throw new Error(`GCS upload failed: ${uploadResponse.statusText}`);
    }

    return { fileId, url: signedUrl.split('?')[0] };
  }

  async downloadFromGCS(fileId) {
    const response = await fetch(`/api/storage/gcs/download/${fileId}`, {
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`GCS download failed: ${response.statusText}`);
    }

    return response.blob();
  }

  async deleteFromGCS(fileId) {
    const response = await fetch(`/api/storage/gcs/delete/${fileId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`GCS delete failed: ${response.statusText}`);
    }

    return response.json();
  }

  async listFromGCS(prefix) {
    const response = await fetch(`/api/storage/gcs/list?prefix=${encodeURIComponent(prefix)}`, {
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`GCS list failed: ${response.statusText}`);
    }

    return response.json();
  }

  // AWS S3 Implementation
  async uploadToS3(file, metadata) {
    // Get presigned URL for upload
    const presignedResponse = await fetch('/api/storage/s3/presigned-url', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify({
        fileName: file.name,
        contentType: file.type,
        metadata: metadata,
        bucketName: this.config.config.bucketName
      })
    });

    if (!presignedResponse.ok) {
      throw new Error('Failed to get presigned URL');
    }

    const { presignedUrl, fileId } = await presignedResponse.json();

    // Upload to S3 using presigned URL
    const uploadResponse = await fetch(presignedUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type
      },
      body: file
    });

    if (!uploadResponse.ok) {
      throw new Error(`S3 upload failed: ${uploadResponse.statusText}`);
    }

    return { fileId, url: presignedUrl.split('?')[0] };
  }

  async downloadFromS3(fileId) {
    const response = await fetch(`/api/storage/s3/download/${fileId}`, {
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`S3 download failed: ${response.statusText}`);
    }

    return response.blob();
  }

  async deleteFromS3(fileId) {
    const response = await fetch(`/api/storage/s3/delete/${fileId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`S3 delete failed: ${response.statusText}`);
    }

    return response.json();
  }

  async listFromS3(prefix) {
    const response = await fetch(`/api/storage/s3/list?prefix=${encodeURIComponent(prefix)}`, {
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`S3 list failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Azure Blob Storage Implementation
  async uploadToAzure(file, metadata) {
    const sasResponse = await fetch('/api/storage/azure/sas-token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify({
        fileName: file.name,
        contentType: file.type,
        metadata: metadata,
        containerName: this.config.config.containerName
      })
    });

    if (!sasResponse.ok) {
      throw new Error('Failed to get SAS token');
    }

    const { sasUrl, fileId } = await sasResponse.json();

    // Upload to Azure using SAS URL
    const uploadResponse = await fetch(sasUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type,
        'x-ms-blob-type': 'BlockBlob'
      },
      body: file
    });

    if (!uploadResponse.ok) {
      throw new Error(`Azure upload failed: ${uploadResponse.statusText}`);
    }

    return { fileId, url: sasUrl.split('?')[0] };
  }

  async downloadFromAzure(fileId) {
    const response = await fetch(`/api/storage/azure/download/${fileId}`, {
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`Azure download failed: ${response.statusText}`);
    }

    return response.blob();
  }

  async deleteFromAzure(fileId) {
    const response = await fetch(`/api/storage/azure/delete/${fileId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`Azure delete failed: ${response.statusText}`);
    }

    return response.json();
  }

  async listFromAzure(prefix) {
    const response = await fetch(`/api/storage/azure/list?prefix=${encodeURIComponent(prefix)}`, {
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`Azure list failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Utility methods
  getAuthToken() {
    // Get authentication token from your auth system
    return localStorage.getItem('authToken') || '';
  }

  async testConnection() {
    try {
      switch (this.provider) {
        case 'secure-db':
          await this.listFromSecureDB('');
          break;
        case 'google-cloud':
          await this.listFromGCS('');
          break;
        case 'aws-s3':
          await this.listFromS3('');
          break;
        case 'azure-blob':
          await this.listFromAzure('');
          break;
        default:
          throw new Error(`Unsupported provider: ${this.provider}`);
      }
      return { success: true, message: 'Connection successful' };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }
}

export default StorageService;
