document.addEventListener('DOMContentLoaded', () => {
    const walletContainer = document.getElementById("walletContainer")
    const metamaskBtn = document.getElementById('metamaskBtn');
    const walletConnectBtn = document.getElementById('walletConnectBtn');
    const statusArea = document.getElementById('statusArea');

    async function switchToARC() { 
        try {
            await window.ethereum.request({
                method: "wallet_switchEthereumChain",
                params: [{ chainId: "0x4cef52" }], // ARC chain ID
            });
        } catch (switchError) {
            // If ARC is not added to MetaMask, add it
            if (switchError.code === 4902) {
                await window.ethereum.request({
                    method: "wallet_addEthereumChain",
                    params: [{
                        chainId: "0x4cef52",
                        chainName: "Arc Testnet",
                        nativeCurrency: {
                            name: "USDC",
                            symbol: "USDC",
                            decimals: 18
                        },
                        rpcUrls: ["https://rpc.testnet.arc.network"],
                        blockExplorerUrls: [" https://testnet.arcscan.app"]
                    }]
                });
            } else {
                console.error(switchError);
            }
        }
    }

    
    function shortAddr(addr){
        if(!addr) return '';
        return addr.slice(0,6) + '…' + addr.slice(-4);
    }


    async function verifyAddr(address, newResource) {
        statusArea.innerHTML = `<div style="margin-top:14px;display:flex;gap:12px;align-items:center"><div class="spinner" aria-hidden="true"></div><div style="color:var(--muted)">Connecting for signature...</div></div>`;

        // Sign nonce
        const nonce = newResource["nonce"]
        const noncePurpose = "auth"
        const message = `Sign this message to authenticate: ${nonce}`;
        const signature = await window.ethereum.request({
            method: 'personal_sign',
            params: [message, address]
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
                wallet: address,
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


    async function connectMetaMask(){
        if (!window.ethereum) {
            renderError('MetaMask not detected. Install MetaMask or use WalletConnect.');
            return;
        }

        try {
            statusArea.innerHTML = `<div style="margin-top:14px;display:flex;gap:12px;align-items:center"><div class="spinner" aria-hidden="true"></div><div style="color:var(--muted)">Connecting to MetaMask...</div></div>`;

            // Request the permissions explicitly, which triggers MetaMask popup
            await window.ethereum.request({
                method: 'wallet_requestPermissions',
                params: [{ eth_accounts: {} }]
            });

            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            const address = accounts[0];

            // Optionally verify chain - you can prompt user to switch networks here
            await switchToARC();

            // Send the address to your backend to create a session / user record:
            const loginUrl = LOGIN_URL; // Replace with your API endpoint
            const postData = {
                method: 'POST', // Specify the HTTP method
                headers: {
                    'Content-Type': 'application/json', // Indicate that you're sending JSON
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    userAddress: address,
                }), // Convert the data to a JSON string
            };
            fetch(loginUrl, postData)
            .then(response => {
                if (!response.ok) {
                throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(newResource => {
                walletContainer.style.display = "none";

                statusArea.innerHTML = `
                <div class="connected" role="status">
                    <div>
                        <div style="font-size:13px;color:var(--muted)">Connected wallet</div>
                        <div class="address" title="${address}">${shortAddr(address)}</div>
                    </div>
                    <div class="actions">
                        <a class="btn primary" id="continueBtn">Verify Address</a>
                    </div>
                </div>
                `;
                document.getElementById('continueBtn').addEventListener('click', async () => await verifyAddr(address, newResource));
            })
            .catch(error => {
                console.error('Error creating resource:', error);
            });
        } catch (err) {
            console.error(err);
            renderError('Connection rejected or failed. Try again.');
        }
    }

    metamaskBtn.addEventListener('click', connectMetaMask);

});