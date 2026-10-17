import React, { useState } from 'react';
import { AlertCircle, Send, X } from 'lucide-react';

const specialties = ['Emergency Medicine', 'Trauma', 'Cardiology', 'Neurology', 'General Medicine'];
const diagnosticTypes = ['CT', 'MRI', 'X-Ray', 'Blood Test', 'Ultrasound'];
const ambulanceEquipment = ['ALS', 'BLS', 'Ventilator', 'Cardiac Equipment'];

const initialForm = {
  name: '',
  age: '',
  gender: 'Unknown',
  emergency_type: '',
  chief_complaint: '',
  symptoms: '',
  condition_description: '',
  heart_rate: '',
  oxygen_saturation: '',
  blood_pressure: '',
  severity_category: 'Unclassified',
  priority: 'P3',
  triage_mode: 'AUTO',
  requires_ambulance: true,
  required_equipment: [],
  required_specialty: 'General Medicine',
  required_diagnostic: '',
  requires_icu: false,
  required_icu_equipment: [],
  requires_ventilator: false,
  arrival_time: '0',
};

function getPatientId() {
  const token = globalThis.crypto?.randomUUID?.().replaceAll('-', '').slice(0, 8)
    || Math.random().toString(36).slice(2, 10);
  return `ER-${Date.now().toString(36).toUpperCase()}-${token.toUpperCase()}`;
}

export default function EmergencyModal({ isOpen, onClose, onSubmit }) {
  const [formData, setFormData] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const setField = (field, value) => setFormData((current) => ({ ...current, [field]: value }));
  const toggleListValue = (field, value) => {
    setFormData((current) => ({
      ...current,
      [field]: current[field].includes(value)
        ? current[field].filter((item) => item !== value)
        : [...current[field], value],
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage('');
    setSubmitting(true);
    const complaintParts = [formData.emergency_type, formData.chief_complaint, formData.symptoms]
      .map((value) => value.trim())
      .filter(Boolean);
    const payload = {
      ...formData,
      id: getPatientId(),
      age: Number(formData.age),
      arrival_time: Number(formData.arrival_time),
      heart_rate: formData.heart_rate === '' ? null : Number(formData.heart_rate),
      oxygen_saturation: formData.oxygen_saturation === '' ? null : Number(formData.oxygen_saturation),
      blood_pressure: formData.blood_pressure.trim() || null,
      condition_description: formData.condition_description.trim() || complaintParts.join('; '),
      required_diagnostic: formData.required_diagnostic || null,
      requires_ventilator: formData.requires_ventilator || formData.required_icu_equipment.includes('ventilator'),
    };
    try {
      await onSubmit(payload);
      setFormData(initialForm);
      onClose();
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || error.message || 'Emergency registration failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && !submitting && onClose()}>
      <section className="modal-panel intake-panel" role="dialog" aria-modal="true" aria-labelledby="emergency-title">
        <header className="modal-heading">
          <div>
            <p className="eyebrow">SYNTHETIC CASE INTAKE</p>
            <h2 id="emergency-title">Register emergency</h2>
            <p>Inputs are passed to the existing triage and resource agents. This is a simulation, not clinical advice.</p>
          </div>
          <button className="icon-button" type="button" aria-label="Close intake" onClick={onClose} disabled={submitting}><X size={19} /></button>
        </header>

        <form className="intake-form" onSubmit={handleSubmit}>
          <fieldset>
            <legend>Patient and presentation</legend>
            <div className="form-grid form-grid-three">
              <label>Patient name<input required maxLength={100} value={formData.name} onChange={(event) => setField('name', event.target.value)} /></label>
              <label>Age<input required type="number" min="0" max="120" value={formData.age} onChange={(event) => setField('age', event.target.value)} /></label>
              <label>Gender<input value={formData.gender} onChange={(event) => setField('gender', event.target.value)} /></label>
            </div>
            <div className="form-grid form-grid-two">
              <label>Emergency type<input value={formData.emergency_type} onChange={(event) => setField('emergency_type', event.target.value)} placeholder="Optional synthetic category" /></label>
              <label>Chief complaint<input value={formData.chief_complaint} onChange={(event) => setField('chief_complaint', event.target.value)} placeholder="Optional" /></label>
            </div>
            <label>Symptoms<textarea rows="2" value={formData.symptoms} onChange={(event) => setField('symptoms', event.target.value)} placeholder="Optional synthetic symptom text" /></label>
            <label>Additional condition description<textarea rows="2" value={formData.condition_description} onChange={(event) => setField('condition_description', event.target.value)} placeholder="Optional; combined with the fields above for rule-based triage" /></label>
          </fieldset>

          <fieldset>
            <legend>Optional reported values</legend>
            <div className="form-grid form-grid-four">
              <label>Heart rate<input type="number" min="0" max="300" value={formData.heart_rate} onChange={(event) => setField('heart_rate', event.target.value)} /></label>
              <label>Oxygen saturation %<input type="number" min="0" max="100" step="0.1" value={formData.oxygen_saturation} onChange={(event) => setField('oxygen_saturation', event.target.value)} /></label>
              <label>Blood pressure<input value={formData.blood_pressure} onChange={(event) => setField('blood_pressure', event.target.value)} placeholder="120/80" /></label>
              <label>Arrival minute<input type="number" min="0" step="0.5" value={formData.arrival_time} onChange={(event) => setField('arrival_time', event.target.value)} /></label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Workflow requirements</legend>
            <div className="form-grid form-grid-two">
              <label>Severity category
                <select value={formData.severity_category} onChange={(event) => setField('severity_category', event.target.value)}>
                  <option value="Unclassified">Auto / needs assessment if unmatched</option>
                  <option value="Critical trauma">Critical trauma (P1)</option>
                  <option value="Critical cardiac">Critical cardiac (P1)</option>
                  <option value="High trauma">High trauma (P2)</option>
                  <option value="Moderate injury">Moderate injury (P3)</option>
                  <option value="Low severity">Low severity (P4)</option>
                </select>
              </label>
              <label>Required doctor specialty
                <select value={formData.required_specialty} onChange={(event) => setField('required_specialty', event.target.value)}>
                  {specialties.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              <label>Diagnostic test
                <select value={formData.required_diagnostic} onChange={(event) => setField('required_diagnostic', event.target.value)}>
                  <option value="">Not required</option>
                  {diagnosticTypes.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
            </div>
            <div className="form-toggle-row">
              <label className="check-label"><input type="checkbox" checked={formData.requires_ambulance} onChange={(event) => setField('requires_ambulance', event.target.checked)} /> Ambulance required</label>
              <label className="check-label"><input type="checkbox" checked={formData.requires_icu} onChange={(event) => setField('requires_icu', event.target.checked)} /> ICU required</label>
            </div>
            {formData.requires_ambulance && (
              <div className="form-check-group">
                <span>Required ambulance capabilities</span>
                {ambulanceEquipment.map((item) => (
                  <label className="check-label" key={item}><input type="checkbox" checked={formData.required_equipment.includes(item)} onChange={() => toggleListValue('required_equipment', item)} /> {item}</label>
                ))}
              </div>
            )}
            {formData.requires_icu && (
              <div className="form-check-group">
                <span>Required ICU equipment</span>
                {['ventilator', 'monitoring'].map((item) => (
                  <label className="check-label" key={item}><input type="checkbox" checked={formData.required_icu_equipment.includes(item)} onChange={() => toggleListValue('required_icu_equipment', item)} /> {item}</label>
                ))}
              </div>
            )}
          </fieldset>

          {errorMessage && <div className="inline-error" role="alert"><AlertCircle size={17} />{errorMessage}</div>}
          <footer className="form-actions">
            <button className="btn btn-secondary" type="button" onClick={onClose} disabled={submitting}>Cancel</button>
            <button className="btn btn-primary" type="submit" disabled={submitting || !formData.emergency_type.trim() && !formData.chief_complaint.trim() && !formData.condition_description.trim() && !formData.symptoms.trim()}>
              <Send size={16} />{submitting ? 'Registering…' : 'Register and orchestrate'}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}