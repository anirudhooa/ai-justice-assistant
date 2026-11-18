document.addEventListener("DOMContentLoaded", () => {
    // Tab Switching
    const navTabs = document.querySelectorAll(".nav-tab");
    const tabPanes = document.querySelectorAll(".tab-pane");

    function switchTab(targetId) {
        navTabs.forEach(t => {
            if (t.getAttribute("data-tab") === targetId) {
                t.classList.add("active");
            } else {
                t.classList.remove("active");
            }
        });

        tabPanes.forEach(p => {
            if (p.id === targetId) {
                p.classList.add("active");
            } else {
                p.classList.remove("active");
            }
        });

        // Lazy load statutes when tab is opened
        if (targetId === "statutes-tab" && !allStatutesLoaded) {
            loadStatutes();
        }
    }

    navTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const targetId = tab.getAttribute("data-tab");
            switchTab(targetId);
        });
    });

    // Top Header Nav Tab Switchers
    document.querySelectorAll("[data-switch-tab]").forEach(link => {
        link.addEventListener("click", (e) => {
            const targetTab = link.getAttribute("data-switch-tab");
            if (targetTab) {
                switchTab(targetTab);
            }
        });
    });

    // Chat Elements
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const messagesContainer = document.getElementById("messages-container");
    const citationsList = document.getElementById("citations-list");
    const activeCountBadge = document.getElementById("active-statute-count");
    const sendBtn = document.getElementById("send-btn");

    // Quick chips
    const chips = document.querySelectorAll(".chip");
    chips.forEach(chip => {
        chip.addEventListener("click", () => {
            const query = chip.getAttribute("data-query");
            userInput.value = query;
            chatForm.dispatchEvent(new Event("submit"));
        });
    });

    // Chat Form Submit
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        // Render User Message
        appendUserMessage(text);
        userInput.value = "";
        userInput.disabled = true;
        sendBtn.disabled = true;

        // Render Loading Indicator
        const loadingId = appendLoadingIndicator();

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: text })
            });

            if (!response.ok) throw new Error("Server error handling query");
            const data = await response.json();

            // Remove loading indicator
            removeLoadingIndicator(loadingId);

            // Render Assistant Response
            appendAssistantMessage(data.answer, data.mode, data.suggested_followups);

            // Update Citations Sidebar
            renderCitations(data.citations);

        } catch (err) {
            removeLoadingIndicator(loadingId);
            appendAssistantMessage(
                "⚠️ **Service Disruption:** Unable to reach the legal knowledge engine. Please check your network connection and try again.",
                "Error",
                []
            );
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
        }
    });

    function appendUserMessage(text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message user-message";
        msgDiv.innerHTML = `
            <div class="msg-avatar">👤</div>
            <div class="msg-body">
                <div class="msg-header">
                    <span class="msg-sender" style="color: #EADBC8;">Citizen Inquiry</span>
                </div>
                <div class="msg-content">${escapeHTML(text)}</div>
            </div>
        `;
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendLoadingIndicator() {
        const id = "loading-" + Date.now();
        const msgDiv = document.createElement("div");
        msgDiv.className = "message assistant-message";
        msgDiv.id = id;
        msgDiv.innerHTML = `
            <div class="msg-avatar">⚖️</div>
            <div class="msg-body">
                <div class="msg-header">
                    <span class="msg-sender">AI Justice Assistant</span>
                    <span class="msg-tag">Searching Indian Codes...</span>
                </div>
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
        return id;
    }

    function removeLoadingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function appendAssistantMessage(markdownText, mode, followups) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message assistant-message";
        
        let parsedHtml = "";
        if (window.marked) {
            parsedHtml = marked.parse(markdownText);
        } else {
            parsedHtml = `<pre>${escapeHTML(markdownText)}</pre>`;
        }

        let followupsHtml = "";
        if (followups && followups.length > 0) {
            followupsHtml = `
                <div style="margin-top: 16px; border-top: 1px dashed var(--border-subtle); padding-top: 12px;">
                    <span style="font-size: 0.74rem; font-weight: 700; color: var(--bronze); text-transform: uppercase; letter-spacing: 0.08em;">Related Legal Inquiries:</span>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                        ${followups.map(f => `<button class="chip followup-chip" style="font-size: 0.75rem;">${escapeHTML(f)}</button>`).join("")}
                    </div>
                </div>
            `;
        }

        msgDiv.innerHTML = `
            <div class="msg-avatar">⚖️</div>
            <div class="msg-body">
                <div class="msg-header">
                    <span class="msg-sender">AI Justice Department Assistant</span>
                    <span class="msg-tag">${escapeHTML(mode || "Official Statutory RAG")}</span>
                </div>
                <div class="msg-content">${parsedHtml}</div>
                ${followupsHtml}
            </div>
        `;
        messagesContainer.appendChild(msgDiv);

        // Bind clicks for followup chips
        msgDiv.querySelectorAll(".followup-chip").forEach(btn => {
            btn.addEventListener("click", () => {
                userInput.value = btn.innerText;
                chatForm.dispatchEvent(new Event("submit"));
            });
        });

        scrollToBottom();
    }

    function renderCitations(citations) {
        if (!citations || citations.length === 0) {
            citationsList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon-wrap">
                        <img src="/static/images/scales-gold.png" alt="Scales of Justice" class="empty-scales-img">
                    </div>
                    <h4 class="empty-title">Statutory Evidence Docket</h4>
                    <p>No direct statutory citations triggered for this specific query.</p>
                </div>
            `;
            activeCountBadge.innerText = "0 Sections Cited";
            return;
        }

        activeCountBadge.innerText = `${citations.length} Section${citations.length > 1 ? 's' : ''} Cited`;
        citationsList.innerHTML = citations.map(c => `
            <div class="statute-card">
                <div class="statute-top">
                    <span class="statute-sec">${escapeHTML(c.section)}</span>
                    <span class="statute-score">Match: ${Math.round(c.relevance_score * 100)}%</span>
                </div>
                <div class="statute-act">${escapeHTML(c.act)}</div>
                ${c.legacy_code ? `<span class="statute-legacy">🔄 Formerly ${escapeHTML(c.legacy_code)}</span>` : ''}
                <div class="statute-title">${escapeHTML(c.title)}</div>
                <div class="statute-summary">${escapeHTML(c.summary)}</div>
                <div class="statute-badges">
                    ${c.cognizable && c.cognizable !== "N/A" ? `<span class="statute-pill pill-cognizable">${escapeHTML(c.cognizable.split(' ')[0])}</span>` : ''}
                    ${c.bailable && c.bailable !== "N/A" ? `<span class="statute-pill pill-bailable">${escapeHTML(c.bailable)}</span>` : ''}
                </div>
                ${c.punishment ? `<div style="font-size: 0.76rem; color: var(--bronze-dark); margin-top: 8px; border-top: 1px dashed var(--border-subtle); padding-top: 6px;"><strong>Statutory Penalty:</strong> ${escapeHTML(c.punishment)}</div>` : ''}
            </div>
        `).join("");
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function escapeHTML(str) {
        if (!str) return "";
        return String(str).replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }

    // TAB 2: BNS ⇄ IPC Code Converter Logic
    const codeSearchInput = document.getElementById("code-search-input");
    const convertBtn = document.getElementById("convert-btn");
    const converterResult = document.getElementById("converter-result-area");
    const codeChips = document.querySelectorAll(".code-chip");

    codeChips.forEach(chip => {
        chip.addEventListener("click", () => {
            codeSearchInput.value = chip.getAttribute("data-code");
            performConversion();
        });
    });

    convertBtn.addEventListener("click", performConversion);
    codeSearchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") performConversion();
    });

    async function performConversion() {
        const query = codeSearchInput.value.trim();
        if (!query) return;

        try {
            const res = await fetch(`/api/convert?code=${encodeURIComponent(query)}`);
            const data = await res.json();

            converterResult.style.display = "block";
            if (!data.found) {
                converterResult.innerHTML = `
                    <div style="text-align: center; color: var(--accent-red); padding: 16px;">
                        <h3 style="font-family: var(--font-display); font-size: 1.3rem;">❌ No Direct Statutory Transition Found</h3>
                        <p style="color: var(--text-secondary); margin-top: 8px; font-size: 0.9rem;">${escapeHTML(data.message)}</p>
                    </div>
                `;
                return;
            }

            converterResult.innerHTML = `
                <div class="conversion-grid">
                    <div class="code-col">
                        <h4>Old Law (Repealed Code)</h4>
                        <div class="law-name" style="color: var(--accent-red);">${escapeHTML(data.legacy_law)}</div>
                    </div>
                    <div class="code-col" style="border-color: var(--bronze); background-color: #FAF6F0;">
                        <h4 style="color: var(--bronze-dark);">Current Reformed Law (In Force)</h4>
                        <div class="law-name" style="color: var(--espresso);">${escapeHTML(data.current_law)}</div>
                    </div>
                </div>
                <div class="converter-details">
                    <h3>${escapeHTML(data.offence_title)}</h3>
                    <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6;">${escapeHTML(data.summary)}</p>
                    <div style="display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap;">
                        <span class="statute-pill pill-cognizable">Status: ${escapeHTML(data.cognizable)}</span>
                        <span class="statute-pill pill-bailable">Bail: ${escapeHTML(data.bailable)}</span>
                    </div>
                    <p style="margin-top: 14px; color: var(--bronze-dark); font-size: 0.88rem;"><strong>Statutory Penalty:</strong> ${escapeHTML(data.punishment)}</p>
                </div>
            `;
        } catch (err) {
            converterResult.style.display = "block";
            converterResult.innerHTML = `<p style="color: var(--accent-red);">Error executing code conversion.</p>`;
        }
    }

    // TAB 3: Law Library Explorer Logic
    let allStatutes = [];
    let allStatutesLoaded = false;
    const statutesGrid = document.getElementById("statutes-grid");
    const filterBtns = document.querySelectorAll(".filter-btn");

    filterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            filterBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const cat = btn.getAttribute("data-category");
            renderLibrary(cat);
        });
    });

    async function loadStatutes() {
        try {
            statutesGrid.innerHTML = `<p style="color: var(--text-muted); text-align: center; grid-column: 1/-1;">Loading curated statutory repository...</p>`;
            const res = await fetch("/api/statutes");
            const data = await res.json();
            allStatutes = data.statutes || [];
            allStatutesLoaded = true;
            const countEl = document.getElementById("statute-count");
            if (countEl) countEl.innerText = allStatutes.length;
            renderLibrary("all");
        } catch (e) {
            statutesGrid.innerHTML = `<p style="color: var(--accent-red);">Failed to load statutory library.</p>`;
        }
    }

    function renderLibrary(category) {
        let filtered = allStatutes;
        if (category !== "all") {
            filtered = allStatutes.filter(s => s.category.toLowerCase().includes(category.toLowerCase()));
        }

        if (filtered.length === 0) {
            statutesGrid.innerHTML = `<p style="color: var(--text-muted); grid-column: 1/-1; text-align: center; padding: 40px 0;">No statutes found for category '${escapeHTML(category)}'.</p>`;
            return;
        }

        statutesGrid.innerHTML = filtered.map(s => `
            <div class="grid-card">
                <div>
                    <div class="grid-card-cat">${escapeHTML(s.category)}</div>
                    <div class="grid-card-sec">${escapeHTML(s.section)}</div>
                    <div class="grid-card-act">${escapeHTML(s.act)}</div>
                    ${s.legacy_code ? `<span class="statute-legacy" style="font-size: 0.72rem;">🔄 ${escapeHTML(s.legacy_code)}</span>` : ''}
                    <div class="grid-card-title">${escapeHTML(s.title)}</div>
                    <div class="grid-card-desc">${escapeHTML(s.summary)}</div>
                </div>
                <div>
                    <div class="statute-badges">
                        ${s.cognizable && s.cognizable !== "N/A" ? `<span class="statute-pill pill-cognizable">${escapeHTML(s.cognizable.split(' ')[0])}</span>` : ''}
                        ${s.bailable && s.bailable !== "N/A" ? `<span class="statute-pill pill-bailable">${escapeHTML(s.bailable)}</span>` : ''}
                    </div>
                    <div class="grid-card-footer">
                        <span><strong>Penalty:</strong> ${escapeHTML(s.punishment || 'Civil Redress / Constitutional Remedy')}</span>
                    </div>
                </div>
            </div>
        `).join("");
    }
});
