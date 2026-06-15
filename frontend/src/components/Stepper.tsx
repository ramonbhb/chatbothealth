interface StepperProps {
  steps: string[];
  current: number;
}

export function Stepper({ steps, current }: StepperProps) {
  return (
    <div className="stepper">
      {steps.map((step, i) => (
        <div key={step} className={`step ${i <= current ? 'active' : ''} ${i === current ? 'current' : ''}`}>
          <span className="step-num">{i + 1}</span>
          <span className="step-label">{step}</span>
        </div>
      ))}
    </div>
  );
}
