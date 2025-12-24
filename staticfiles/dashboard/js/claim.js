import { ABI } from "./abi.js";

document.addEventListener('DOMContentLoaded', () => {
    const logBox = document.getElementById("logBox");

    // READ-ONLY RPC (no MetaMask involvement)
    const rpc = "https://rpc.testnet.arc.network";
    const web3 = new Web3(rpc);

    const CONTRACT_ADDRESS = LOAN_CONTRACT_ADDRESS;
    let contract = new web3.eth.Contract(ABI, CONTRACT_ADDRESS);

    async function claimLoan() {
        document.getElementById("claimBtn").style.display = "none";

        let item = document.createElement("div");
        item.className = "log-item";
        item.textContent = "Finalizing claim on-chain…";
        logBox.appendChild(item);

        setTimeout(() => {
            document.getElementById("successMsg").style.display = "block";
        }, 1500);
    }

    document.getElementById("claimBtn").onclick = async () => {
        const onchainloanID = ONCHAIN_LOAN_ID;
        const wallet = WALLET;
        const url = CLAIM_URL;


        try {
            // USE METAMASK ONLY FOR TX SENDING
            const signer = new Web3(window.ethereum);

            await window.ethereum.request({ method: "eth_requestAccounts" });

            const signedContract = new signer.eth.Contract(ABI, CONTRACT_ADDRESS);

            const tx = await signedContract.methods.withdrawLoan(Number(onchainloanID)).send({
                from: wallet,
                gas: 300000
            });

            const options = {
                method: 'POST', // Specify the HTTP method
                headers: {
                    'Content-Type': 'application/json', // Inform the server about the data type
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
                },
            };

            fetch(url, options)
            .then(response => {
                if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json(); // Parse the JSON response from the server
            })
            .then(responseData => {
                if (responseData.status == "success"){
                    console.log("Loan withdrawn:", tx.transactionHash);
                    claimLoan();
                }

            })
            .catch(error => {
                console.error('Error:', error); // Handle any errors during the request
            });

            
        } catch (e) {
            console.error(e);
            alert("Failed to withdraw loan");
        }
    };
});
