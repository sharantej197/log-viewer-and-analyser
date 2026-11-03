function downloadfile(){
    k = document.createElement('a');
    k.href = "/filedownload";
    k.download="LogAnalysis.csv";
    k.click();

}
function visual(){
    k=document.createElement('a');
    k.href="/DataVisualisation";
    k.click();
}
function filter() {
    let filterE=document.getElementById("Esfilter").value;
    let filterL=document.getElementById("Lsfilter").value;
    let table=document.getElementById("table");
    let tr=table.getElementsByTagName("tr");
    for (let i=1; i < tr.length; i++) {
          tr[i].style.display="";
        }
    for (let i=1; i < tr.length; i++) {
      let td2=tr[i].getElementsByTagName("td")[2]
      let td4=tr[i].getElementsByTagName("td")[4]
        let there4=td4.innerText;
        let there2=td2.innerText;
        tr[i].style.display=((filterL === "" || there2 === filterL) && (filterE === "" || there4 === filterE))?"":"none";
      }
}
