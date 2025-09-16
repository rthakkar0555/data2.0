// Simple test script to verify backend connection
const API_BASE_URL = 'http://localhost:8000';

async function testBackend() {
  console.log('Testing backend connection...');
  
  try {
    // Test health check
    console.log('1. Testing health check...');
    const healthResponse = await fetch(`${API_BASE_URL}/health/`);
    if (healthResponse.ok) {
      const healthData = await healthResponse.json();
      console.log('✅ Health check passed:', healthData);
    } else {
      console.log('❌ Health check failed:', healthResponse.status);
      return;
    }
    
    // Test companies endpoint
    console.log('2. Testing companies endpoint...');
    const companiesResponse = await fetch(`${API_BASE_URL}/companies/`);
    if (companiesResponse.ok) {
      const companiesData = await companiesResponse.json();
      console.log('✅ Companies endpoint working:', companiesData);
    } else {
      console.log('❌ Companies endpoint failed:', companiesResponse.status);
    }
    
    // Test uploaded files endpoint
    console.log('3. Testing uploaded files endpoint...');
    const filesResponse = await fetch(`${API_BASE_URL}/get_uploaded_files/`);
    if (filesResponse.ok) {
      const filesData = await filesResponse.json();
      console.log('✅ Uploaded files endpoint working:', filesData);
    } else {
      console.log('❌ Uploaded files endpoint failed:', filesResponse.status);
    }
    
    console.log('🎉 Backend connection test completed!');
    
  } catch (error) {
    console.error('❌ Backend connection failed:', error.message);
    console.log('Make sure the backend server is running on port 8000');
  }
}

// Run the test
testBackend();
