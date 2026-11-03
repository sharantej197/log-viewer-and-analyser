function checkfilter(){
    const fromdate = document.getElementById("fromdate").value;
    const todate = document.getElementById("todate").value;
    const fromtime = document.getElementById("fromtime").value;
    const totime = document.getElementById("totime").value;
    const notice = document.getElementById("hide");
    if (!fromdate || !todate || !fromtime || !totime) {
        notice.hidden = false;
        return false;
    }
    notice.hidden = true;
    return true;
}
