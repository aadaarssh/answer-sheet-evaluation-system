// Test script to verify upload workflow triggers Celery tasks
const API_BASE_URL = 'http://localhost:8000';
const fs = require('fs');
const path = require('path');

// Mock form data for testing
async function testUploadWorkflow() {
  try {
    console.log('🧪 Testing Upload Workflow with Task Triggering...\n');

    // Step 1: Login
    console.log('1️⃣ Authenticating...');
    const loginData = new FormData();
    loginData.append('username', 'test@university.edu');
    loginData.append('password', 'testpassword123');

    const loginResponse = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      body: loginData,
    });

    if (!loginResponse.ok) {
      throw new Error('Login failed');
    }

    const authData = await loginResponse.json();
    console.log('✅ Login successful');

    // Step 2: Create a test scheme
    console.log('\n2️⃣ Creating test evaluation scheme...');
    const schemeData = {
      scheme_name: 'Test Math Exam',
      subject: 'Mathematics',
      total_marks: 100,
      passing_marks: 40,
      questions: [
        {
          question_number: 1,
          max_marks: 100,
          concepts: [
            {
              concept: 'Mathematical problem solving',
              keywords: ['solve', 'calculate', 'answer', 'equation'],
              weight: 1.0,
              marks_allocation: 100
            }
          ]
        }
      ]
    };

    const schemeResponse = await fetch(`${API_BASE_URL}/api/schemes/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authData.access_token}`
      },
      body: JSON.stringify(schemeData),
    });

    if (!schemeResponse.ok) {
      const error = await schemeResponse.json();
      throw new Error(`Scheme creation failed: ${error.detail}`);
    }

    const scheme = await schemeResponse.json();
    console.log('✅ Test scheme created:', scheme.id);

    // Step 3: Create a test session
    console.log('\n3️⃣ Creating test session...');
    const sessionData = {
      session_name: 'Test Upload Session',
      scheme_id: scheme.id
    };

    const sessionResponse = await fetch(`${API_BASE_URL}/api/sessions/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authData.access_token}`
      },
      body: JSON.stringify(sessionData),
    });

    if (!sessionResponse.ok) {
      const error = await sessionResponse.json();
      throw new Error(`Session creation failed: ${error.detail}`);
    }

    const session = await sessionResponse.json();
    console.log('✅ Test session created:', session.id);

    // Step 4: Create a dummy image file for testing
    console.log('\n4️⃣ Creating test image file...');
    
    // Create a simple base64 image (1x1 white pixel PNG)
    const testImageBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==';
    const testImageBuffer = Buffer.from(testImageBase64, 'base64');
    
    // Create FormData for file upload
    const uploadFormData = new FormData();
    uploadFormData.append('session_id', session.id);
    
    // Create a blob from the buffer (simulating file upload)
    const imageBlob = new Blob([testImageBuffer], { type: 'image/png' });
    uploadFormData.append('files', imageBlob, 'test_student_answer.png');

    console.log('✅ Test image file created');

    // Step 5: Upload file and check for task triggering
    console.log('\n5️⃣ Uploading file and checking task triggering...');
    
    const uploadResponse = await fetch(`${API_BASE_URL}/api/scripts/upload-batch`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authData.access_token}`
      },
      body: uploadFormData,
    });

    if (!uploadResponse.ok) {
      const error = await uploadResponse.json();
      throw new Error(`Upload failed: ${error.detail}`);
    }

    const uploadResult = await uploadResponse.json();
    console.log('📄 Upload response:', JSON.stringify(uploadResult, null, 2));

    // Step 6: Check if tasks were triggered
    if (uploadResult.processing_tasks && uploadResult.processing_tasks.length > 0) {
      console.log('✅ Tasks were triggered successfully!');
      
      const firstTask = uploadResult.processing_tasks[0];
      console.log(`📋 First task ID: ${firstTask.task_id}`);
      
      // Step 7: Check task status
      console.log('\n6️⃣ Checking task status...');
      const taskStatusResponse = await fetch(`${API_BASE_URL}/api/scripts/task/${firstTask.task_id}/status`, {
        headers: {
          'Authorization': `Bearer ${authData.access_token}`
        }
      });

      if (taskStatusResponse.ok) {
        const taskStatus = await taskStatusResponse.json();
        console.log('📊 Task status:', JSON.stringify(taskStatus, null, 2));
        console.log('✅ Task status endpoint working!');
      } else {
        console.log('⚠️ Could not fetch task status');
      }

    } else {
      console.log('❌ No tasks were triggered. Check Celery worker status.');
    }

    console.log('\n🎉 Upload workflow test completed!');

  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Check if we're running Node.js with fetch support
if (typeof fetch === 'undefined') {
  console.log('⚠️ This test requires Node.js 18+ with fetch support or a browser environment');
  console.log('To run: node --experimental-fetch test-upload-workflow.js');
} else {
  testUploadWorkflow();
}