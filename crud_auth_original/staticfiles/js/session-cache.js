/* Se conserva sólo información de presentación; Django mantiene la sesión en su cookie. */
(function () {
    const user = document.querySelector('.user-tools span');
    if (!user) return;
    const username = user.textContent.replace(/^\s*HOLA,\s*/i, '').trim();
    if (!username) return;
    localStorage.setItem('deimos.session.user', username);
    localStorage.setItem('deimos.session.cachedAt', new Date().toISOString());
    document.querySelectorAll('a[href*="/accounts/logout/"]').forEach((link) => {
        link.addEventListener('click', () => {
            localStorage.removeItem('deimos.session.user');
            localStorage.removeItem('deimos.session.cachedAt');
        });
    });
})();
