// Aquí puedes agregar cualquier funcionalidad adicional que necesites
// Por ejemplo, manejar los clics en los botones de edición

document.querySelectorAll('.edit-button').forEach(button => {
    button.addEventListener('click', function() {
        const criteriaName = this.previousElementSibling.textContent;
        console.log(`Editing: ${criteriaName}`);
        // Aquí puedes agregar la lógica para editar el criterio
    });
});

document.querySelectorAll('.expand-button').forEach(button => {
    button.addEventListener('click', function() {
        const sectionId = this.getAttribute('data-section') + '-details';
        const containerId = this.getAttribute('data-section') + '-container';
        const detailsSection = document.getElementById(sectionId);
        const detailcontainer = document.getElementById(containerId);
        if (detailsSection.style.display === 'none') {
            detailsSection.style.display = 'block';
            detailcontainer.style.display = 'block';
            this.textContent = 'Collapse';
        } else {
            detailsSection.style.display = 'none';
            detailcontainer.style.display = 'none';
            this.textContent = 'Expand';
        }
    });
});