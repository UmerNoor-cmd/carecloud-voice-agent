const app = {
  patients: [],
  calls: [],
  appointments: [],

  init() {
    this.setupTabs();
    this.setupGlobalFormatters();
    this.refreshAll();
    // Poll every 10 seconds for real-time live call updates
    setInterval(() => {
      this.loadCalls();
      this.loadAppointments();
    }, 10000);
  },

  setupTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', () => {
        navItems.forEach(n => n.classList.remove('active'));
        item.classList.add('active');

        const tabId = item.dataset.tab;
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        const activePane = document.getElementById(tabId);
        if (activePane) activePane.classList.add('active');

        const headings = {
          'patients-tab': ['Patient Directory', 'Persisted demographic records collected via voice telephony agent & REST API'],
          'calls-tab': ['Call Logs & Transcripts', 'Transcripts and metadata captured from telephone intake calls'],
          'appointments-tab': ['Appointments Schedule', 'Appointments scheduled after patient intake confirmation'],
          'simulator-tab': ['Voice Intake Simulator', 'Test tool calling, duplicate detection, and REST API database writes']
        };

        if (headings[tabId]) {
          document.getElementById('page-heading').innerText = headings[tabId][0];
          document.getElementById('page-subheading').innerText = headings[tabId][1];
        }
      });
    });
  },

  // Setup input formatting & integer-only restrictions
  setupGlobalFormatters(container = document) {
    // 1. Phone numbers: only digits, formatted as 555-123-4567, max 10 digits
    container.querySelectorAll('.format-phone').forEach(el => {
      el.addEventListener('input', (e) => {
        let digits = e.target.value.replace(/\D/g, '');
        if (digits.length > 10) digits = digits.slice(0, 10);
        
        let formatted = digits;
        if (digits.length > 6) {
          formatted = `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
        } else if (digits.length > 3) {
          formatted = `${digits.slice(0, 3)}-${digits.slice(3)}`;
        }
        e.target.value = formatted;
      });
    });

    // 2. Zip codes: only digits, max 5 (or 9 for zip+4)
    container.querySelectorAll('.format-zip').forEach(el => {
      el.addEventListener('input', (e) => {
        let val = e.target.value.replace(/[^\d-]/g, '');
        let digits = val.replace(/\D/g, '');
        if (digits.length > 9) digits = digits.slice(0, 9);

        if (digits.length > 5) {
          e.target.value = `${digits.slice(0, 5)}-${digits.slice(5)}`;
        } else {
          e.target.value = digits;
        }
      });
    });

    // 3. Date of birth: only digits, auto MM/DD/YYYY
    container.querySelectorAll('.format-dob').forEach(el => {
      el.addEventListener('input', (e) => {
        let digits = e.target.value.replace(/\D/g, '');
        if (digits.length > 8) digits = digits.slice(0, 8);

        let formatted = digits;
        if (digits.length > 4) {
          formatted = `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
        } else if (digits.length > 2) {
          formatted = `${digits.slice(0, 2)}/${digits.slice(2)}`;
        }
        e.target.value = formatted;
      });
    });

    // 4. State: only 2 uppercase letters
    container.querySelectorAll('.format-state').forEach(el => {
      el.addEventListener('input', (e) => {
        let letters = e.target.value.replace(/[^a-zA-Z]/g, '').toUpperCase();
        if (letters.length > 2) letters = letters.slice(0, 2);
        e.target.value = letters;
      });
    });

    // 5. Names: only alphabetic characters, hyphens, apostrophes, and spaces
    container.querySelectorAll('.format-name').forEach(el => {
      el.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/[^a-zA-Z\s'-]/g, '');
      });
    });
  },

  async refreshAll() {
    await Promise.all([
      this.loadPatients(),
      this.loadCalls(),
      this.loadAppointments()
    ]);
  },

  async loadPatients() {
    const lastName = document.getElementById('filter-last-name')?.value.trim() || '';
    const dob = document.getElementById('filter-dob')?.value.trim() || '';
    const phone = document.getElementById('filter-phone')?.value.trim() || '';
    const includeDeleted = document.getElementById('filter-include-deleted')?.checked || false;

    const params = new URLSearchParams();
    if (lastName) params.append('last_name', lastName);
    if (dob) params.append('date_of_birth', dob);
    if (phone) params.append('phone_number', phone);
    if (includeDeleted) params.append('include_deleted', 'true');

    try {
      const res = await fetch(`/patients?${params.toString()}`);
      const data = await res.json();
      if (data && data.data) {
        this.patients = data.data;
        this.renderPatientsTable(this.patients);
        document.getElementById('stat-total-patients').innerText = this.patients.length;
        document.getElementById('patient-count-badge').innerText = this.patients.length;
      }
    } catch (err) {
      console.error('Failed to load patients:', err);
    }
  },

  renderPatientsTable(patients) {
    const tbody = document.getElementById('patients-tbody');
    if (!patients || patients.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8">No matching patient records found.</td></tr>`;
      return;
    }

    tbody.innerHTML = patients.map(p => {
      const isDeleted = Boolean(p.deleted_at);
      const statusBadge = isDeleted
        ? `<span class="pill-badge deleted">Soft-Deleted</span>`
        : `<span class="pill-badge active">Active</span>`;

      return `
        <tr style="${isDeleted ? 'opacity: 0.6;' : ''}">
          <td>
            <div class="patient-name-cell">
              <span class="patient-full-name">${this.escape(p.first_name)} ${this.escape(p.last_name)}</span>
              <span class="patient-id-sub">${p.patient_id.slice(0, 8)}...</span>
            </div>
          </td>
          <td>${this.escape(p.date_of_birth)}</td>
          <td>${this.escape(p.sex)}</td>
          <td class="font-mono">${this.escape(p.phone_number)}</td>
          <td>${this.escape(p.address_line_1)}, ${this.escape(p.city)}, ${this.escape(p.state)} ${this.escape(p.zip_code)}</td>
          <td>${p.insurance_provider ? this.escape(p.insurance_provider) : '<span style="color:var(--text-faint)">None</span>'}</td>
          <td>${statusBadge}</td>
          <td>
            <div style="display:flex;gap:0.4rem;">
              <button class="btn btn-secondary btn-sm" onclick="app.viewPatient('${p.patient_id}')">View</button>
              ${isDeleted
                ? `<button class="btn btn-success btn-sm" onclick="app.restorePatient('${p.patient_id}')">Restore</button>`
                : `<button class="btn btn-danger btn-sm" onclick="app.softDeletePatient('${p.patient_id}')">Delete</button>`
              }
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  async loadCalls() {
    try {
      const res = await fetch('/calls');
      const data = await res.json();
      if (data && data.data) {
        this.calls = data.data;
        document.getElementById('stat-total-calls').innerText = this.calls.length;
        this.renderCallsTable(this.calls);
      }
    } catch (err) {
      console.error('Failed to load call logs:', err);
    }
  },

  renderCallsTable(calls) {
    const tbody = document.getElementById('calls-tbody');
    if (!calls || calls.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8">No voice calls recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = calls.map(c => `
      <tr>
        <td class="font-mono" style="font-size:0.8rem;">${c.created_at ? new Date(c.created_at).toLocaleString() : 'N/A'}</td>
        <td class="font-mono">${this.escape(c.caller_phone || 'Web/Unknown')}</td>
        <td>${c.duration_seconds || 0}s</td>
        <td>${c.patient_id ? `<span class="pill-badge active">Linked</span>` : '<span style="color:var(--text-faint)">Unlinked</span>'}</td>
        <td>${this.escape(c.summary || 'Call completed')}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="app.viewTranscript('${c.id}')">View Transcript</button>
        </td>
      </tr>
    `).join('');
  },

  async loadAppointments() {
    try {
      const res = await fetch('/appointments');
      const data = await res.json();
      if (data && data.data) {
        this.appointments = data.data;
        document.getElementById('stat-total-appts').innerText = this.appointments.length;
        this.renderAppointmentsTable(this.appointments);
      }
    } catch (err) {
      console.error('Failed to load appointments:', err);
    }
  },

  renderAppointmentsTable(appts) {
    const tbody = document.getElementById('appts-tbody');
    if (!appts || appts.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8">No appointments scheduled yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = appts.map(a => `
      <tr>
        <td class="font-mono" style="font-size:0.8rem;">${a.patient_id.slice(0, 8)}...</td>
        <td><strong>${this.escape(a.department)}</strong></td>
        <td>${this.escape(a.appointment_date)}</td>
        <td>${this.escape(a.appointment_time)}</td>
        <td><span class="pill-badge scheduled">${this.escape(a.status)}</span></td>
        <td style="color:var(--text-muted);font-size:0.82rem;">${this.escape(a.notes || 'N/A')}</td>
      </tr>
    `).join('');
  },

  // View / Edit Patient Modal
  viewPatient(patientId) {
    const p = this.patients.find(item => item.patient_id === patientId);
    if (!p) return;

    document.getElementById('modal-title').innerText = `${p.first_name} ${p.last_name}`;
    document.getElementById('modal-body-content').innerHTML = `
      <div id="modal-error-banner" class="error-banner" style="display:none;"></div>
      <form onsubmit="app.updatePatient(event, '${p.patient_id}')">
        <div class="form-row">
          <div class="form-group">
            <label>First Name *</label>
            <input type="text" id="edit-fn" class="format-name" value="${this.escape(p.first_name)}" required maxlength="50">
          </div>
          <div class="form-group">
            <label>Last Name *</label>
            <input type="text" id="edit-ln" class="format-name" value="${this.escape(p.last_name)}" required maxlength="50">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Date of Birth * (MM/DD/YYYY)</label>
            <input type="text" id="edit-dob" class="format-dob" inputmode="numeric" value="${this.escape(p.date_of_birth)}" required maxlength="10">
          </div>
          <div class="form-group">
            <label>Sex *</label>
            <select id="edit-sex">
              <option value="Male" ${p.sex === 'Male' ? 'selected' : ''}>Male</option>
              <option value="Female" ${p.sex === 'Female' ? 'selected' : ''}>Female</option>
              <option value="Other" ${p.sex === 'Other' ? 'selected' : ''}>Other</option>
              <option value="Decline to Answer" ${p.sex === 'Decline to Answer' ? 'selected' : ''}>Decline to Answer</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Phone Number * (10 Digits Only)</label>
            <input type="text" id="edit-phone" class="format-phone" inputmode="numeric" value="${this.escape(p.phone_number)}" required maxlength="12" placeholder="555-123-4567">
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" id="edit-email" value="${this.escape(p.email || '')}" placeholder="patient@example.com">
          </div>
        </div>
        <div class="form-group">
          <label>Address Line 1 *</label>
          <input type="text" id="edit-addr1" value="${this.escape(p.address_line_1)}" required maxlength="255">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>City *</label>
            <input type="text" id="edit-city" value="${this.escape(p.city)}" required maxlength="100">
          </div>
          <div class="form-group" style="flex:0.5;">
            <label>State * (2-letter)</label>
            <input type="text" id="edit-state" class="format-state" value="${this.escape(p.state)}" maxlength="2" required placeholder="FL">
          </div>
          <div class="form-group" style="flex:0.7;">
            <label>Zip Code * (5 digits)</label>
            <input type="text" id="edit-zip" class="format-zip" inputmode="numeric" value="${this.escape(p.zip_code)}" required maxlength="10" placeholder="33101">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Insurance Provider</label>
            <input type="text" id="edit-ins" value="${this.escape(p.insurance_provider || '')}">
          </div>
          <div class="form-group">
            <label>Member ID</label>
            <input type="text" id="edit-ins-id" value="${this.escape(p.insurance_member_id || '')}">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Emergency Contact Name</label>
            <input type="text" id="edit-em-name" class="format-name" value="${this.escape(p.emergency_contact_name || '')}">
          </div>
          <div class="form-group">
            <label>Emergency Contact Phone (10 digits)</label>
            <input type="text" id="edit-em-phone" class="format-phone" inputmode="numeric" value="${this.escape(p.emergency_contact_phone || '')}" maxlength="12" placeholder="555-987-6543">
          </div>
        </div>
        <div style="font-size:0.75rem;color:var(--text-faint);margin-bottom:1rem;" class="font-mono">
          Patient UUID: ${p.patient_id}<br>
          Created: ${p.created_at} | Updated: ${p.updated_at}
        </div>
        <div style="display:flex;justify-content:flex-end;gap:0.75rem;">
          <button type="button" class="btn btn-secondary" onclick="app.closeModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Save Changes (PUT /patients)</button>
        </div>
      </form>
    `;
    this.setupGlobalFormatters(document.getElementById('modal-body-content'));
    document.getElementById('patient-modal').style.display = 'flex';
  },

  async updatePatient(e, patientId) {
    e.preventDefault();
    const errorBanner = document.getElementById('modal-error-banner');
    errorBanner.style.display = 'none';

    const payload = {
      first_name: document.getElementById('edit-fn').value,
      last_name: document.getElementById('edit-ln').value,
      date_of_birth: document.getElementById('edit-dob').value,
      sex: document.getElementById('edit-sex').value,
      phone_number: document.getElementById('edit-phone').value,
      email: document.getElementById('edit-email').value || null,
      address_line_1: document.getElementById('edit-addr1').value,
      city: document.getElementById('edit-city').value,
      state: document.getElementById('edit-state').value,
      zip_code: document.getElementById('edit-zip').value,
      insurance_provider: document.getElementById('edit-ins').value || null,
      insurance_member_id: document.getElementById('edit-ins-id').value || null,
      emergency_contact_name: document.getElementById('edit-em-name').value || null,
      emergency_contact_phone: document.getElementById('edit-em-phone').value || null,
    };

    try {
      const res = await fetch(`/patients/${patientId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok && data.data) {
        this.closeModal();
        await this.loadPatients();
      } else {
        this.showFormError(errorBanner, data);
      }
    } catch (err) {
      errorBanner.style.display = 'block';
      errorBanner.innerText = `Network Error: ${err.message}`;
    }
  },

  async softDeletePatient(patientId) {
    if (!confirm('Are you sure you want to soft-delete this patient record?')) return;
    try {
      const res = await fetch(`/patients/${patientId}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok) {
        await this.loadPatients();
      } else {
        alert(`Failed to delete: ${JSON.stringify(data.error)}`);
      }
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  },

  async restorePatient(patientId) {
    try {
      const res = await fetch(`/patients/${patientId}/restore`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        await this.loadPatients();
      } else {
        alert(`Failed to restore: ${JSON.stringify(data.error)}`);
      }
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  },

  openNewPatientModal() {
    document.getElementById('modal-title').innerText = 'Register New Patient';
    document.getElementById('modal-body-content').innerHTML = `
      <div id="modal-error-banner" class="error-banner" style="display:none;"></div>
      <form onsubmit="app.createNewPatient(event)">
        <div class="form-row">
          <div class="form-group">
            <label>First Name * (Letters only)</label>
            <input type="text" id="new-fn" class="format-name" placeholder="John" required maxlength="50">
          </div>
          <div class="form-group">
            <label>Last Name * (Letters only)</label>
            <input type="text" id="new-ln" class="format-name" placeholder="Doe" required maxlength="50">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Date of Birth * (MM/DD/YYYY - Digits only)</label>
            <input type="text" id="new-dob" class="format-dob" inputmode="numeric" placeholder="05/14/1990" required maxlength="10">
          </div>
          <div class="form-group">
            <label>Sex *</label>
            <select id="new-sex">
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
              <option value="Decline to Answer">Decline to Answer</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Phone Number * (10 Digits Only)</label>
            <input type="text" id="new-phone" class="format-phone" inputmode="numeric" placeholder="555-123-4567" required maxlength="12">
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" id="new-email" placeholder="patient@example.com">
          </div>
        </div>
        <div class="form-group">
          <label>Address Line 1 *</label>
          <input type="text" id="new-addr1" placeholder="123 Health Ave" required maxlength="255">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>City *</label>
            <input type="text" id="new-city" placeholder="Miami" required maxlength="100">
          </div>
          <div class="form-group" style="flex:0.5;">
            <label>State * (2 letters)</label>
            <input type="text" id="new-state" class="format-state" placeholder="FL" maxlength="2" required>
          </div>
          <div class="form-group" style="flex:0.7;">
            <label>Zip Code * (5 digits only)</label>
            <input type="text" id="new-zip" class="format-zip" inputmode="numeric" placeholder="33101" required maxlength="10">
          </div>
        </div>
        <div style="display:flex;justify-content:flex-end;gap:0.75rem;margin-top:1.25rem;">
          <button type="button" class="btn btn-secondary" onclick="app.closeModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Create Patient (POST /patients)</button>
        </div>
      </form>
    `;
    this.setupGlobalFormatters(document.getElementById('modal-body-content'));
    document.getElementById('patient-modal').style.display = 'flex';
  },

  showFormError(bannerEl, data) {
    bannerEl.style.display = 'block';
    if (data.error && data.error.details && data.error.details.length > 0) {
      const msgs = data.error.details.map(d => `• <strong>${d.field || 'Field'}</strong>: ${d.message}`).join('<br>');
      bannerEl.innerHTML = `<strong>Please correct the following:</strong><br>${msgs}`;
    } else if (data.error && data.error.message) {
      bannerEl.innerHTML = `<strong>Validation Error:</strong> ${data.error.message}`;
    } else {
      bannerEl.innerHTML = `<strong>Error:</strong> ${JSON.stringify(data.detail || data)}`;
    }
  },

  async createNewPatient(e) {
    e.preventDefault();
    const errorBanner = document.getElementById('modal-error-banner');
    errorBanner.style.display = 'none';

    const payload = {
      first_name: document.getElementById('new-fn').value,
      last_name: document.getElementById('new-ln').value,
      date_of_birth: document.getElementById('new-dob').value,
      sex: document.getElementById('new-sex').value,
      phone_number: document.getElementById('new-phone').value,
      email: document.getElementById('new-email').value || null,
      address_line_1: document.getElementById('new-addr1').value,
      city: document.getElementById('new-city').value,
      state: document.getElementById('new-state').value,
      zip_code: document.getElementById('new-zip').value
    };

    try {
      const res = await fetch('/patients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.status === 201 && data.data) {
        this.closeModal();
        await this.loadPatients();
      } else {
        this.showFormError(errorBanner, data);
      }
    } catch (err) {
      errorBanner.style.display = 'block';
      errorBanner.innerText = `Network Error: ${err.message}`;
    }
  },

  // Transcript viewer
  viewTranscript(callId) {
    const call = this.calls.find(c => c.id === callId);
    if (!call) return;

    document.getElementById('transcript-modal-body').innerHTML = `
      <div style="margin-bottom:1rem;">
        <strong>Caller:</strong> ${this.escape(call.caller_phone || 'Unknown')}<br>
        <strong>Duration:</strong> ${call.duration_seconds}s<br>
        <strong>Summary:</strong> ${this.escape(call.summary || 'N/A')}
      </div>
      ${call.recording_url ? `
        <div style="margin-bottom:1rem;">
          <label style="display:block;font-size:0.8rem;color:var(--text-muted);margin-bottom:0.35rem;">Audio Recording Playback:</label>
          <audio controls src="${call.recording_url}" style="width:100%;"></audio>
        </div>
      ` : ''}
      <label style="display:block;font-size:0.8rem;color:var(--text-muted);margin-bottom:0.35rem;">Full Intake Transcript:</label>
      <div class="sim-result-box" style="max-height:300px;overflow-y:auto;">
        ${this.escape(call.transcript || 'No transcript text available for this call.')}
      </div>
    `;
    document.getElementById('transcript-modal').style.display = 'flex';
  },

  closeModal() {
    document.getElementById('patient-modal').style.display = 'none';
  },

  closeTranscriptModal() {
    document.getElementById('transcript-modal').style.display = 'none';
  },

  // Simulator
  async simCheckPhone() {
    const phone = document.getElementById('sim-phone').value;
    const resBox = document.getElementById('sim-duplicate-result');
    resBox.style.display = 'block';
    resBox.innerHTML = 'Executing tool: check_existing_patient...';

    try {
      const res = await fetch('/vapi/webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: {
            type: 'tool-calls',
            toolCalls: [{
              id: 'sim_tool_1',
              type: 'function',
              function: {
                name: 'check_existing_patient',
                arguments: { phone_number: phone }
              }
            }]
          }
        })
      });
      const data = await res.json();
      resBox.innerText = JSON.stringify(data, null, 2);
    } catch (err) {
      resBox.innerText = `Error: ${err.message}`;
    }
  },

  async simRegisterPatient(e) {
    e.preventDefault();
    const resBox = document.getElementById('sim-register-result');
    resBox.style.display = 'block';
    resBox.innerText = 'Executing tool: register_patient via Webhook...';

    const payload = {
      first_name: document.getElementById('sim-fn').value,
      last_name: document.getElementById('sim-ln').value,
      date_of_birth: document.getElementById('sim-dob').value,
      sex: document.getElementById('sim-sex').value,
      phone_number: document.getElementById('sim-reg-phone').value,
      email: document.getElementById('sim-email').value || null,
      address_line_1: document.getElementById('sim-addr1').value,
      city: document.getElementById('sim-city').value,
      state: document.getElementById('sim-state').value,
      zip_code: document.getElementById('sim-zip').value,
      insurance_provider: document.getElementById('sim-ins').value || null,
      insurance_member_id: document.getElementById('sim-ins-id').value || null
    };

    try {
      const res = await fetch('/vapi/webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: {
            type: 'tool-calls',
            toolCalls: [{
              id: 'sim_tool_reg_1',
              type: 'function',
              function: {
                name: 'register_patient',
                arguments: payload
              }
            }]
          }
        })
      });
      const data = await res.json();
      resBox.innerText = JSON.stringify(data, null, 2);
      await this.loadPatients();
    } catch (err) {
      resBox.innerText = `Error: ${err.message}`;
    }
  },

  escape(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, m => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    })[m]);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  app.init();
});
