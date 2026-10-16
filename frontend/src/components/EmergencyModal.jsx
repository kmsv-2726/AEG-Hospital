import React, { useState } from 'react';
import { X, AlertTriangle, Send } from 'lucide-react';

export default function EmergencyModal({ isOpen, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    name: 'Sarah Connor',
    age: 29,
    gender: 'Female',
    condition_description: 'Acute thoracic pain, suspected rib fracture and pneumothorax',
    severity_category: 'High trauma',
    priority: 'P2',
    requires_ambulance: true,
    required_specialty: 'Trauma',
    required_diagnostic: 'X-Ray',
    requires_icu: false,
    arrival_time: 12.0,
  });

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const pid = `P${Math.floor(100 + Math.random() * 900)}`;
    onSubmit({
      ...formData,
      id: pid,
      age: Number(formData.age),
      arrival_time: Number(formData.arrival_time),
    });
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '560px',
        background: '#0f172a',
        border: '1px solid rgba(6, 182, 212, 0.3)',
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.6)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'rgba(239, 68, 68, 0.2)', padding: '6px', borderRadius: '8px' }}>
              <AlertTriangle size={20} color="var(--rose-danger)" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>Register Synthetic Emergency</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Simulate real-time emergency dispatch and agent allocation</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '10px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Patient Name</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                style={{ width: '100%', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Age</label>
              <input
                type="number"
                required
                value={formData.age}
                onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                style={{ width: '100%', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Gender</label>
              <select
                value={formData.gender}
                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                style={{ width: '100%', padding: '8px 12px', background: '#090d16', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Condition Description</label>
            <textarea
              required
              rows={2}
              value={formData.condition_description}
              onChange={(e) => setFormData({ ...formData, condition_description: e.target.value })}
              style={{ width: '100%', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem', resize: 'none' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Severity Category</label>
              <select
                value={formData.severity_category}
                onChange={(e) => setFormData({ ...formData, severity_category: e.target.value })}
                style={{ width: '100%', padding: '8px 12px', background: '#090d16', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
              >
                <option value="Critical trauma">Critical trauma (P1)</option>
                <option value="Critical cardiac">Critical cardiac (P1)</option>
                <option value="High trauma">High trauma (P2)</option>
                <option value="Moderate injury">Moderate injury (P3)</option>
                <option value="Low severity">Low severity (P4)</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Required Doctor Specialty</label>
              <select
                value={formData.required_specialty}
                onChange={(e) => setFormData({ ...formData, required_specialty: e.target.value })}
                style={{ width: '100%', padding: '8px 12px', background: '#090d16', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
              >
                <option value="Trauma">Trauma</option>
                <option value="Cardiology">Cardiology</option>
                <option value="General Medicine">General Medicine</option>
                <option value="Emergency Medicine">Emergency Medicine</option>
                <option value="Neurology">Neurology</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Diagnostic Scan</label>
              <select
                value={formData.required_diagnostic || ''}
                onChange={(e) => setFormData({ ...formData, required_diagnostic: e.target.value || null })}
                style={{ width: '100%', padding: '8px 12px', background: '#090d16', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
              >
                <option value="">None Required</option>
                <option value="X-Ray">X-Ray</option>
                <option value="CT">CT Scan</option>
                <option value="MRI">MRI Scan</option>
                <option value="Ultrasound">Ultrasound</option>
                <option value="Blood Test">Blood Test Lab</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Simulated Arrival Min</label>
              <input
                type="number"
                step="0.5"
                value={formData.arrival_time}
                onChange={(e) => setFormData({ ...formData, arrival_time: e.target.value })}
                style={{ width: '100%', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '20px', padding: '8px 0' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer', color: '#e2e8f0' }}>
              <input
                type="checkbox"
                checked={formData.requires_ambulance}
                onChange={(e) => setFormData({ ...formData, requires_ambulance: e.target.checked })}
              />
              Requires Ambulance Dispatch
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer', color: '#e2e8f0' }}>
              <input
                type="checkbox"
                checked={formData.requires_icu}
                onChange={(e) => setFormData({ ...formData, requires_icu: e.target.checked })}
              />
              Requires ICU Bed
            </label>
          </div>

          {/* Buttons */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              <Send size={15} />
              <span>Submit to Multi-Agent System</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
