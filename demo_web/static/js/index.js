const serverAddress = "https://tadpole-dashing-ape.ngrok-free.app";

function showStatus(message, isError = false) {
  const statusElement = document.getElementById('status');
  statusElement.textContent = message;
  if (isError) {
      statusElement.style.color = 'red';
  } else {
      statusElement.style.color = 'green';
  }
}

function showLoginContainer() {
  document.getElementById('start-container').style.display = 'none';
  document.getElementById('login-container').style.display = 'block';
}

function showRegisterContainer() {
  document.getElementById('start-container').style.display = 'none';
  document.getElementById('register-container').style.display = 'block';
}

function login() {
  document.getElementById('login-container').style.display = 'none';
  document.getElementById('upload-container').style.display = 'block';
}

document.getElementById('uploadBtn').addEventListener('click', async () => {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;
    if (!files.length) {
      showStatus('請選擇至少一個檔案！', true);
      return;
    }
  
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
  
    try {
      showStatus('正在上傳...');
      const response = await fetch(`${serverAddress}/api/upload`, {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        showStatus(`上傳失敗：${result.error}`, true);
        return;
      }
      
      showStatus('上傳成功！');
      fileInput.value = '';
    } catch (err) {
      console.error(err);
      showStatus('連接服務器失敗，請檢查服務器地址是否正確', true);
    } 
  });
  