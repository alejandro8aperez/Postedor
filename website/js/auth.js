(function () {
    var USER = 'admin';
    var PASS = 'admin12345';
    var KEY = 'movelty_auth';
    var path = window.location.pathname;
    var file = (path.split('/').pop() || '').toLowerCase();
    var inPages = /\/pages\/$/.test(path.substring(0, path.lastIndexOf('/') + 1));
    var toLogin = (inPages ? '../' : '') + 'login.html';
    var toHome = (inPages ? '../' : '') + 'index.html';

    function hasSession() {
        try { return sessionStorage.getItem(KEY) === 'ok'; }
        catch (e) { return false; }
    }

    if (file !== 'login.html' && !hasSession()) {
        window.location.replace(toLogin);
        return;
    }
    if (file === 'login.html' && hasSession()) {
        window.location.replace(toHome);
        return;
    }

    if (file !== 'login.html') {
        document.addEventListener('DOMContentLoaded', function () {
            var nav = document.querySelector('.navbar .navbar-inner');
            if (nav && !document.getElementById('movelty-logout')) {
                var a = document.createElement('a');
                a.id = 'movelty-logout';
                a.href = '#';
                a.textContent = 'Salir';
                a.style.cssText = 'color:#fff;font-size:0.85rem;text-decoration:none;border:1px solid rgba(255,255,255,0.4);padding:6px 12px;border-radius:20px;margin-left:12px;transition:background .2s;';
                a.addEventListener('mouseenter', function () { a.style.background = 'rgba(255,255,255,0.15)'; });
                a.addEventListener('mouseleave', function () { a.style.background = 'transparent'; });
                a.addEventListener('click', function (e) {
                    e.preventDefault();
                    try { sessionStorage.removeItem(KEY); } catch (err) {}
                    window.location.replace(toLogin);
                });
                nav.appendChild(a);
            }
        });
        return;
    }

    document.addEventListener('DOMContentLoaded', function () {
        var form = document.getElementById('login-form');
        if (!form) return;
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var u = document.getElementById('username').value.trim();
            var p = document.getElementById('password').value;
            if (u === USER && p === PASS) {
                try { sessionStorage.setItem(KEY, 'ok'); } catch (err) {}
                window.location.replace(toHome);
            } else {
                var err = document.getElementById('login-error');
                if (err) err.style.display = 'block';
            }
        });
    });
})();