document.addEventListener('DOMContentLoaded', function() {
  // Add click event for the main verification button
  const mainVerifyButton = document.getElementById('main-verify-product-btn');
  if (mainVerifyButton) {
    mainVerifyButton.addEventListener('click', function() {
      const productIdInput = document.getElementById('main-product-id-input');
      const verificationResult = document.getElementById('main-verification-result');
      const alertDiv = verificationResult.querySelector('.alert');
      
      verifyProduct(productIdInput.value, verificationResult, alertDiv);
    });
  }
  
  // Add click events for individual product verify buttons
  const verifyButtons = document.querySelectorAll('.verify-product-btn');
  verifyButtons.forEach(button => {
    button.addEventListener('click', function() {
      const productId = this.getAttribute('data-product-id');
      const container = this.closest('.verify-product-container');
      const resultDiv = container.querySelector('.verification-result');
      const alertDiv = resultDiv.querySelector('.alert');
      
      verifyProduct(productId, resultDiv, alertDiv);
    });
  });
  
  // Product verification function
  function verifyProduct(productId, resultDiv, alertDiv) {
    if (!productId.trim()) {
      showResult('Please enter a Product ID', 'warning', resultDiv, alertDiv);
      return;
    }
    
    // Show loading state
    showResult('Verifying product on blockchain...', 'info', resultDiv, alertDiv);
    
    // In a production environment, this would call your backend API
    // For this demo, we'll simulate API calls with setTimeout
    const backendUrl = 'http://localhost:8000/get_product_details/';
    
    // Simulating a fetch call
    simulateFetch(backendUrl + productId)
      .then(response => {
        // Based on product ID, show different responses
        const verifiedProducts = ['NIKE-AIR-123456', 'LV-BAG-345678', 'GUCCI-SUN-567890'];
        const suspiciousProducts = ['ADIDAS-BOOST-789012', 'ROLEX-SUB-678901'];
        
        if (verifiedProducts.includes(productId)) {
          showResult(
            `✅ LEGIT VERIFIED<br>
            Product ID: ${productId}<br>
            Manufacturer: GD23ZFKW4QLVX3TMDXE...PSJ3<br>
            Current Owner: Sixteen Clothing Store<br>
            Registered: ${new Date().toLocaleString()}<br><br>
            <small>Verified on Stellar/Soroban blockchain</small>`,
            'success', resultDiv, alertDiv
          );
        } else if (suspiciousProducts.includes(productId)) {
          showResult(
            `⚠️ SUSPICIOUS PRODUCT<br>
            Product ID: ${productId}<br>
            This product could not be verified in the blockchain registry.<br>
            It may be counterfeit or tampered with.`,
            'danger', resultDiv, alertDiv
          );
        } else {
          // For demo purposes, we'll consider unknown products as not found
          showResult('Product not found. This product may be counterfeit or not registered in our blockchain.', 'danger', resultDiv, alertDiv);
        }
      })
      .catch(error => {
        showResult('Error connecting to verification service. Please try again later.', 'danger', resultDiv, alertDiv);
        console.error('Verification error:', error);
      });
  }
  
  // Helper function to show results
  function showResult(message, type, resultDiv, alertDiv) {
    resultDiv.style.display = 'block';
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = message;
  }
  
  // Simulating fetch for the demo
  function simulateFetch(url) {
    return new Promise((resolve, reject) => {
      console.log('Simulating fetch to:', url);
      setTimeout(() => {
        if (Math.random() > 0.1) { // 10% chance of error for realism
          resolve({ success: true });
        } else {
          reject(new Error('Network error'));
        }
      }, 1500); // Simulate network delay
    });
  }
});