interface StepperProps {
  steps: string[];
  current: number;
  onStepClick?: (index: number) => void;
}

export function Stepper({ steps, current, onStepClick }: StepperProps) {
  return (
    <div className="stepper">
      {steps.map((step, i) => (
        <button
          key={step}
          type="button"
          className={`step ${i <= current ? 'active' : ''} ${i === current ? 'current' : ''}`}
          onClick={() => onStepClick?.(i)}
          disabled={!onStepClick}
        >
          <span className="step-num">{i + 1}</span>
          <span className="step-label">{step}</span>
        </button>
      ))}
    </div>
  );
}
