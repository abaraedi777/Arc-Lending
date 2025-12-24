document.addEventListener('DOMContentLoaded', () => {

    const cb1 = document.getElementById("cb-confirm");
    const cb2 = document.getElementById("cb-authorize");
    const submitBtn = document.getElementById("confirm-btn");

    function updateButtonState() {
        // Enable button only if both checkboxes are checked
        submitBtn.disabled = !(cb1.checked && cb2.checked);
    }


    async function kycConsent() {
        // Sign nonce
        const nonce = NONCE
        const noncePurpose = "kyc_consent"
        const message = `Sign this message to Consent: ${nonce}`;
        const signature = await window.ethereum.request({
            method: 'personal_sign',
            params: [message, WALLET]
        });

        // Verify signature on backend
        const verificationUrl = VERIFICATION_URL; // Replace with your API endpoint
        const postData = {
            method: 'POST', // Specify the HTTP method
            headers: {
                'Content-Type': 'application/json', // Indicate that you're sending JSON
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                wallet: WALLET,
                signature: signature,
                purpose: noncePurpose,
            }), // Convert the data to a JSON string
        };
        fetch(verificationUrl, postData)
        .then(response => {
            if (!response.ok) {
            throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(response => {
            if (response.redirect && response.success) {
                window.location.href = response.redirect;
            }
        })
        .catch(error => {
            console.error('Error creating resource:', error);
        });
    }

    // Listen for changes on both checkboxes
    cb1.addEventListener("change", updateButtonState);
    cb2.addEventListener("change", updateButtonState);
    submitBtn.addEventListener("click", kycConsent);

});