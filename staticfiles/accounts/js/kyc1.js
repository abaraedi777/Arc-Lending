document.addEventListener('DOMContentLoaded', () => {
    function short(addr){
        return addr.slice(0,6) + '…' + addr.slice(-4);
    }

    document.getElementById('walletAddr').textContent = short(WALLET);
});