function openDeleteModal(element) {
    const itemId = element.getAttribute('data-id');
    const itemInfo = element.getAttribute('data-info');
    const deleteUrl = element.getAttribute('data-url');
    
    document.getElementById('deleteModal').style.display = 'block';
    document.getElementById('deleteMessage').textContent = 'Vai tiešām vēlaties izdzēst: ' + itemInfo + '?';
    document.getElementById('deleteForm').action = deleteUrl;
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

window.onclick = function(event) {
    var modal = document.getElementById('deleteModal');
    if (event.target == modal) {
        closeDeleteModal();
    }
}

// Attiestata datuma filtrus uz šodienas datumu un iesniedz formu
function atgutDatumu() {
    // Iegūst šodienas datumu
    var today = new Date();
    var tagadejaisMenesis = today.getMonth() + 1;
    var tagadejaisGads = today.getFullYear();
    
    // Atiestata visus izvēlnes laukus uz tekošo mēnesi un gadu
    document.getElementById('sakuma_menesis').value = tagadejaisMenesis;
    document.getElementById('sakuma_gads').value = tagadejaisGads;
    document.getElementById('beigu_menesis').value = tagadejaisMenesis;
    document.getElementById('beigu_gads').value = tagadejaisGads;
    
    document.getElementById('periodForm').submit();
}