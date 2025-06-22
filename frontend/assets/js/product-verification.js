/**
 * Project Legit - Product Verification System
 * This file handles the blockchain verification of products
 */

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
    
    // Backend API'sine istek gönder
    fetch(`http://localhost:8000/get_product_details/${productId}`)
      .then(response => {
        if (!response.ok) {
          if (response.status === 404) {
            // Ürün bulunamadı, suspicious badge göster
            updateProductBadge(productId, 'suspicious');
            showResult('Product not found. This product may be counterfeit or not registered.', 'danger', resultDiv, alertDiv);
            return Promise.reject('Product not found');
          } else {
            updateProductBadge(productId, 'suspicious');
            showResult('Error verifying product. Please try again later.', 'danger', resultDiv, alertDiv);
            return Promise.reject('Server error');
          }
        }
        return response.json();
      })
      .then(data => {
        // Backend'den başarılı yanıt aldık, ürün blockchain'de doğrulandı
        // Legit badge göster
        updateProductBadge(productId, 'legit');
        
        showResult(
          `✅ LEGIT VERIFIED<br>
          Product ID: ${data.product_id}<br>
          Manufacturer: ${data.manufacturer.substring(0, 10)}...${data.manufacturer.substring(data.manufacturer.length - 5)}<br>
          Current Owner: ${data.current_owner.substring(0, 10)}...${data.current_owner.substring(data.current_owner.length - 5)}<br>
          Registered: ${new Date(data.registered_at * 1000).toLocaleString()}<br><br>
          <small>Verified on Stellar/Soroban blockchain</small>`,
          'success', resultDiv, alertDiv
        );
      })
      .catch(error => {
        console.error('Verification error:', error);
        // Hata zaten işlendi, ek bir şey yapmaya gerek yok
      });
  }
  
  // Helper function to update product badge
  function updateProductBadge(productId, status) {
    const badge = document.getElementById(`badge-${productId}`);
    if (badge) {
      badge.style.display = 'block';
      
      if (status === 'legit') {
        badge.className = 'legit-badge';
        badge.innerText = 'LEGIT VERIFIED';
      } else {
        badge.className = 'suspicious-badge';
        badge.innerText = 'SUSPICIOUS';
      }
    }
  }
  
  // Helper function to show results
  function showResult(message, type, resultDiv, alertDiv) {
    resultDiv.style.display = 'block';
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = message;
  }
});