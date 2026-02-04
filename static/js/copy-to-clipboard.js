(function() {
  'use strict';

  if(!document.queryCommandSupported('copy')) {
    return;
  }

  var copyIcon = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M16 1H6a2 2 0 0 0-2 2v12h2V3h10V1zm3 4H10a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm0 16H10V7h9v14z"/></svg>';
  var checkIcon = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M9 16.2l-3.5-3.5L4 14.2l5 5 12-12-1.4-1.4z"/></svg>';
  var errorIcon = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 15h-2v-2h2zm0-4h-2V7h2z"/></svg>';

  function flashCopyMessage(el, state) {
    if (state === 'success') {
      el.innerHTML = checkIcon;
      el.setAttribute('aria-label', 'Copied');
      el.setAttribute('data-state', 'success');
    } else if (state === 'error') {
      el.innerHTML = errorIcon;
      el.setAttribute('aria-label', 'Copy failed');
      el.setAttribute('data-state', 'error');
    } else {
      el.innerHTML = copyIcon;
      el.setAttribute('aria-label', 'Copy');
      el.setAttribute('data-state', 'idle');
    }

    if (state) {
      setTimeout(function() {
        flashCopyMessage(el, null);
      }, 1000);
    }
  }

  function selectText(node) {
    var selection = window.getSelection();
    var range = document.createRange();
    range.selectNodeContents(node);
    selection.removeAllRanges();
    selection.addRange(range);
    return selection;
  }

  function addCopyButton(containerEl) {
    var copyBtn = document.createElement("button");
    copyBtn.className = "highlight-copy-btn";
    copyBtn.type = "button";
    flashCopyMessage(copyBtn, null);

    var codeEl = containerEl.firstElementChild;
    copyBtn.addEventListener('click', function() {
      try {
        var selection = selectText(codeEl);
        document.execCommand('copy');
        selection.removeAllRanges();

        flashCopyMessage(copyBtn, 'success')
      } catch(e) {
        console && console.log(e);
        flashCopyMessage(copyBtn, 'error')
      }
    });

    containerEl.appendChild(copyBtn);
  }

  // Add copy button to code blocks
  var highlightBlocks = document.getElementsByClassName('highlight');
  Array.prototype.forEach.call(highlightBlocks, addCopyButton);
})();