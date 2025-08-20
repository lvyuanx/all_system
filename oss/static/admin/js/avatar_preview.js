document.addEventListener('DOMContentLoaded', function () {
    const avatarInput = document.getElementById('id_avatar');
    const previewImg = document.getElementById('avatar-preview');

    if (!avatarInput || !previewImg) return;

    avatarInput.addEventListener('change', function (event) {
        const file = event.target.files[0];
        if (file) {
            const url = URL.createObjectURL(file);
            previewImg.src = url;
            previewImg.style.display = 'block';
        } else {
            previewImg.src = '';
            previewImg.style.display = 'none';
        }
    });
});
