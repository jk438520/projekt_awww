function openTab(tabClass, tabID) {
    var i;
    var x = document.getElementsByClassName(tabClass);
    for (i = 0; i < x.length; i++) {
        x[i].style.display = "none";
    }
    document.getElementById(tabID).style.display = "flex";
}
