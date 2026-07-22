"""
BlueCrack Constants
====================
Shared constant values and JavaScript injection strings for BlueCrack.
"""

from typing import List

CSS_PATH_JS: str = """
function cssPath(el){
    if(!el) return null;
    var p=[];
    while(el.nodeType===1){
        var s=el.nodeName.toLowerCase();
        if(el.id){
            s+='#'+el.id;
            p.unshift(s);
            break;
        } else {
            var sib=el, n=1;
            while(sib=sib.previousElementSibling){
                if(sib.nodeName.toLowerCase()==s) n++;
            }
            if(n!=1) s+=':nth-of-type('+n+')';
        }
        p.unshift(s);
        el=el.parentNode;
    }
    return p.join(' > ');
}
return cssPath(arguments[0]);
"""

AUTO_DETECT_JS: str = """
window._autoFindFields = function() {
    let passwordField = document.querySelector('input[type="password"]');
    let userField = null;
    if (passwordField) {
        let inputs = Array.from(
            passwordField.form
                ? passwordField.form.querySelectorAll('input')
                : document.querySelectorAll('input')
        );
        for (let el of inputs) {
            if ((el.type === 'text' || el.type === 'email' || el.name.includes('user')) && el !== passwordField) {
                userField = el;
                break;
            }
        }
    }
    let ucss = userField
        ? userField.tagName.toLowerCase() + (userField.id ? '#'+userField.id : (userField.name ? '[name="'+userField.name+'"]' : ''))
        : null;
    let pcss = passwordField
        ? passwordField.tagName.toLowerCase() + (passwordField.id ? '#'+passwordField.id : (passwordField.name ? '[name="'+passwordField.name+'"]' : ''))
        : null;
    return [ucss, pcss];
};
"""

CLICK_LISTENER_JS: str = """
document.addEventListener('click', function(e){ window._lastClicked = e.target; });
"""

DEFAULT_USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

DEFAULT_LIMIT_TEXT: str = "too many requests"

# ANSI color helpers (for CLI output)
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_BLUE = "\033[34m"
_RESET = "\033[0m"
_BOLD = "\033[1m"

try:
    import keyboard  # noqa: F401
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

try:
    import stem  # noqa: F401
    HAS_STEM = True
except ImportError:
    HAS_STEM = False

