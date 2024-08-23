function handleFileUpload(inputId, listId) {
    document.getElementById(inputId).addEventListener('change', function(event) {
        var fileList = document.getElementById(listId);
        fileList.innerHTML = '';
        
        if (this.files && this.files.length > 0) {
            for (var i = 0; i < this.files.length; i++) {
                var fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                
                var fileIcon = document.createElement('div');
                fileIcon.className = 'triangle';
                
                var fileName = document.createElement('span');
                fileName.className = 'file-name';
                fileName.textContent = this.files[i].name;
                
                fileItem.appendChild(fileIcon);
                fileItem.appendChild(fileName);
                fileList.appendChild(fileItem);
            }
        } else {
            fileList.innerHTML = 'No files selected';
        }
    });
}

function uploadFiles() {
    const applicationFiles = document.getElementById('file-upload-application').files;
    const historyFiles = document.getElementById('file-upload-history').files;
    
    if (applicationFiles.length === 0 && historyFiles.length === 0) {
        alert("Por favor, cargue la aplicación de crédito y los estados de cuenta.");
        return;
    }
    
    if (applicationFiles.length === 0) {
        alert("Por favor, cargue la aplicación de crédito.");
        return;
    }
    
    if (historyFiles.length === 0) {
        alert("Por favor, cargue los estados de cuenta.");
        return;
    }
    
    const formData = new FormData();
    
    for (let i = 0; i < applicationFiles.length; i++) {
        formData.append('application', applicationFiles[i]);
    }
    
    for (let i = 0; i < historyFiles.length; i++) {
        formData.append('history', historyFiles[i]);
    }
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.status === 200) {
            // Limpiar los archivos si la respuesta es exitosa
            document.getElementById('file-upload-application').value = '';
            document.getElementById('file-upload-history').value = '';
            document.getElementById('file-list-application').innerHTML = '';
            document.getElementById('file-list-history').innerHTML = '';
            alert("Archivos subidos exitosamente.");
        } else {
            throw new Error('Error en la subida de archivos');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Hubo un error al subir los archivos.");
    });
}

// Inicializar los manejadores de carga de archivos
handleFileUpload('file-upload-application', 'file-list-application');
handleFileUpload('file-upload-history', 'file-list-history');

// Agregar el evento click al botón de subida
document.querySelector('.send-button').addEventListener('click', uploadFiles);