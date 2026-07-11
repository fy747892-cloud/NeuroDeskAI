type ModulePlaceholderProps = {
  description: string;
  items: Array<{
    label: string;
    value: string;
  }>;
};

export function ModulePlaceholder({ description, items }: ModulePlaceholderProps) {
  return (
    <section className="moduleSurface">
      <p className="moduleLead">{description}</p>
      <div className="moduleGrid">
        {items.map((item) => (
          <article className="moduleCard" key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </article>
        ))}
      </div>
    </section>
  );
}
