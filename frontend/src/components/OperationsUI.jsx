import React from 'react';

export function PageHeader({ eyebrow, title, description, actions }) {
  return (
    <div className="page-header-row">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1 className="page-heading">{title}</h1>
        {description && <p className="page-subtitle">{description}</p>}
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </div>
  );
}

export function StatTile({ label, value, detail, icon: Icon, tone = 'teal' }) {
  return (
    <section className="stat-tile">
      <div className="stat-copy">
        <span className="stat-label">{label}</span>
        <strong className="stat-value">{value}</strong>
        {detail && <small>{detail}</small>}
      </div>
      {Icon && <span className={`stat-icon tone-${tone}`}><Icon size={19} /></span>}
    </section>
  );
}

export function SectionTitle({ title, description, actions }) {
  return (
    <div className="section-title-row">
      <div>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {actions && <div>{actions}</div>}
    </div>
  );
}

export function EmptyState({ title, description }) {
  return <div className="empty-state"><strong>{title}</strong><span>{description}</span></div>;
}
