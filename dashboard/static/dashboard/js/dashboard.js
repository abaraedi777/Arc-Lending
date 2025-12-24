import { ABI } from "./abi.js";
import { USDC_ABI } from "./usdc_abi.js";

document.addEventListener('DOMContentLoaded', () => {
    const loanDuration = document.getElementById("duration");
    const loanAmount = document.getElementById("amount");
    const borrowBtn = document.getElementById("borrow-btn");
    const repaymentTotal = document.getElementById("repaymentTotal");
    

    function updateRepayment() {
        if (Number(loanAmount.value) > 0) {
            let interest = Number(loanAmount.value) * 10 * (Number(loanDuration.value) / 365)
            let totalRepay = Number(loanAmount.value) + interest
            repaymentTotal.innerText = totalRepay.toFixed(2);
        } 
    }

    loanDuration.addEventListener("change", updateRepayment);
    loanAmount.addEventListener("input", updateRepayment);


    // DEPOSIT FUNCTIONALITY DepositWithdrawalTotal
    const depositBtn = document.getElementById("deposit-btn");
    const depoField = document.getElementById("Depositamount");
    const depoDuration = document.getElementById("Depositduration");
    const depoAPR = document.getElementById("DepositWithdrawalTotal");
    let DepoistAmount;
    let DepoistInterest;
    let DepoistDuration = document.getElementById("Depositduration").value;

    function normalizeUSDC(n) {
        return (Math.floor(Number(n) * 1e6) / 1e6).toFixed(6)
    }

    function toUSDC(n) {
        const rpc = "https://rpc.testnet.arc.network";
        const web3 = new Web3(rpc);

        return web3.utils.toBN(
            web3.utils.toWei(normalizeUSDC(n), "mwei")
        )
    }

    function updateDepositAmount() {
        DepoistAmount = Number(document.getElementById("Depositamount").value)

        DepoistInterest = DepoistAmount * 5 * (Number(depoDuration.value) / 365)

        const total = DepoistAmount + DepoistInterest;

        depoAPR.innerText = total.toFixed(2);

        DepoistDuration = depoDuration.value;

    }
    

    async function DepositFunction() {
        if (Number(DepoistAmount) < 1 || DepoistAmount == undefined ) {
            console.log("HERE")
            return
        }

        depositBtn.disabled = true;

        try {
            const web3 = new Web3(window.ethereum);

            const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
            const user = accounts[0];

            // Contract
            const contract = new web3.eth.Contract(ABI, LOAN_CONTRACT_ADDRESS);

            // USDC Contract
            const USDC_TOKEN_ADDRESS = "0x3600000000000000000000000000000000000000"
            const usdc = new web3.eth.Contract(USDC_ABI, USDC_TOKEN_ADDRESS);

            // 1. Approve USDC for repayment
            if (user == WALLET) {
                const amount   = toUSDC(DepoistAmount)
                const interest = toUSDC(DepoistInterest)

                await usdc.methods
                    .approve(LOAN_CONTRACT_ADDRESS, amount)
                    .send({ from: WALLET, gas: 300000 });

                // 2. Deposit Funds
                const receipt  = await contract.methods
                    .createDeposit("USDC", amount, interest)
                    .send({ from: WALLET, gas: 300000 });

                const depoURL = DEPO_URL;

                // The event emitted in your Solidity contract
                const depositEvent = receipt.events.DepositCreated;

                const options = {
                    method: 'POST', // Specify the HTTP method
                    headers: {
                        'Content-Type': 'application/json', // Inform the server about the data type
                        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        onchainDepoID: Number(depositEvent.returnValues.DepositId),
                        wallet: WALLET,
                        amount: DepoistAmount,
                        interest: DepoistInterest,
                        asset: "USDC",
                        duration: DepoistDuration
                    })
                };

                fetch(depoURL, options)
                .then(response => {
                    if (!response.ok) {
                    throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(response => {
                    if (response.status == "success") {
                        console.log("HERE")
                        setTimeout(() => {
                            location.reload();
                        }, 5000);
                    }
                })
                .catch(error => {
                    console.error('Error creating resource:', error);
                });

                
            } else {
                console.log("NO")
            }
        

        } catch (e) {
            console.error("Deposit error:", e);
            alert("Deposit failed.");
        }
    }

    depositBtn.addEventListener("click", DepositFunction)
    depoField.addEventListener("input", updateDepositAmount);
    depoDuration.addEventListener("change", updateDepositAmount);

});



// repay function
window.repayFunction = async function(loanOnchainId, amountToRepay, loanID) {
    try {
        const web3 = new Web3(window.ethereum);

        const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
        const user = accounts[0];

        // Loan Contract
        const loan = new web3.eth.Contract(ABI, LOAN_CONTRACT_ADDRESS);

        // USDC Contract
        const USDC_TOKEN_ADDRESS = "0x3600000000000000000000000000000000000000"
        const usdc = new web3.eth.Contract(USDC_ABI, USDC_TOKEN_ADDRESS);

        if (user == WALLET) {
            // 1. Approve USDC for repayment
            let amount = Number(amountToRepay) * 10**6
            await usdc.methods
                .approve(LOAN_CONTRACT_ADDRESS, amount)
                .send({ from: WALLET, gas: 500000 });

            await new Promise(r => setTimeout(r, 3000))

            // 2. Repay Loan
            await loan.methods
                .repayLoan(loanOnchainId)
                .send({ from: WALLET, gas: 500000 });

            const repayLoanURL = REPAY_LOAN_URL;

            const options = {
                method: 'POST', // Specify the HTTP method
                headers: {
                    'Content-Type': 'application/json', // Inform the server about the data type
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    loanID: loanID,
                })
            };

            fetch(repayLoanURL, options)
            .then(response => {
                if (!response.ok) {
                throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(response => {
                if (response.status == "success") {
                    console.log("HERE")
                    setTimeout(() => {
                        location.reload();
                    }, 5000);
                }
            })
            .catch(error => {
                console.error('Error creating resource:', error);
            });
        }
        
    } catch (e) {
        console.error("Repay error:", e);
        alert("Repay failed.");
    }
}





// deposit withdrawn function
window.withdrawDepositFunction = async function(depositOnchainId, amount, interest, DjangoDueDate) {
    function parseDjangoDate(str) {
        return new Date(
            str
            .replace('.', '')      // Dec. -> Dec
            .replace(' a.m.', ' AM')
            .replace(' p.m.', ' PM')
            .replace(',', '')      // remove first comma
        )
    }

    function normalizeUSDC(n) {
        return (Math.floor(Number(n) * 1e6) / 1e6).toFixed(6)
    }

    function toUSDC(n) {
        const rpc = "https://rpc.testnet.arc.network";
        const web3 = new Web3(rpc);

        return web3.utils.toBN(
            web3.utils.toWei(normalizeUSDC(n), "mwei")
        )
    }

    try {
        const web3 = new Web3(window.ethereum);

        const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
        const user = accounts[0];

        // Loan Contract
        const contract = new web3.eth.Contract(ABI, LOAN_CONTRACT_ADDRESS);

        // USDC Contract
        const USDC_TOKEN_ADDRESS = "0x3600000000000000000000000000000000000000"
        const usdc = new web3.eth.Contract(USDC_ABI, USDC_TOKEN_ADDRESS);

        const dueDate = parseDjangoDate(DjangoDueDate)
        const now = new Date()

        let amountToWithdraw;
        if (now >= dueDate) {
            amountToWithdraw = Number(amount) + Number(interest)
        } else {
            amountToWithdraw = Number(amount) + (Number(interest) * 0.5)
        }



        if (user == WALLET) {
            // Withdraw from contract
            await contract.methods
                .withdrawDeposit(depositOnchainId, toUSDC(amountToWithdraw))
                .send({ from: WALLET, gas: 300000 });

            const depowithdrawURL = DEPO_WITHDRAW_URL;

            const options = {
                method: 'POST', // Specify the HTTP method
                headers: {
                    'Content-Type': 'application/json', // Inform the server about the data type
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    onchainDepoID: depositOnchainId,
                    wallet: WALLET,
                    withdrawnAmount: amountToWithdraw
                })
            };

            fetch(depowithdrawURL, options)
            .then(response => {
                if (!response.ok) {
                throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(response => {
                if (response.status == "success") {
                    console.log("HERE")
                    setTimeout(() => {
                        location.reload();
                    }, 5000);
                }
            })
            .catch(error => {
                console.error('Error creating resource:', error);
            });
        }

        
        
    } catch (e) {
        console.error("Deposit Withdrawal error:", e);
        alert("Deposit Withdrawal failed.");
    }
}