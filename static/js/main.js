function openDeleteModal(element) {
    const itemInfo = element.getAttribute('data-info');
    const deleteUrl = element.getAttribute('data-url');


    document.getElementById('deleteMessage').textContent = 'Vai tiešām vēlaties izdzēst: ' + itemInfo + '?';
    document.getElementById('deleteForm').action = deleteUrl;

    const modalElement = document.getElementById('deleteModal');

    const modal = new bootstrap.Modal(modalElement);
    modal.show();
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