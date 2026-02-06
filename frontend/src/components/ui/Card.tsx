import { type HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { Mood } from '../../types';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'highlighted' | 'outlined';
  mood?: Mood;
  hoverable?: boolean;
}

const moodBorderColors: Record<Mood, string> = {
  tense: 'border-mood-tense',
  calm: 'border-mood-calm',
  mysterious: 'border-mood-mysterious',
  triumphant: 'border-mood-triumphant',
  somber: 'border-mood-somber',
  humorous: 'border-mood-humorous',
  urgent: 'border-mood-urgent',
  peaceful: 'border-mood-peaceful',
  neutral: 'border-primary/20',
};

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', mood, hoverable = false, children, ...props }, ref) => {
    const baseStyles = 'rounded-lg transition-all duration-200';

    const variants = {
      default: 'bg-background-secondary border border-primary/20 shadow-lg',
      highlighted: 'bg-background-secondary border-2 border-primary shadow-glow-primary',
      outlined: 'bg-transparent border border-primary/30',
    };

    const moodBorder = mood ? moodBorderColors[mood] : '';
    const hoverStyles = hoverable ? 'hover:border-primary/50 hover:shadow-xl cursor-pointer' : '';

    return (
      <div
        ref={ref}
        className={twMerge(clsx(baseStyles, variants[variant], moodBorder, hoverStyles, className))}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={twMerge('px-4 py-3 border-b border-primary/10', className)}
      {...props}
    />
  )
);

CardHeader.displayName = 'CardHeader';

export interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {}

export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={twMerge('font-heading text-lg text-primary', className)}
      {...props}
    />
  )
);

CardTitle.displayName = 'CardTitle';

export interface CardContentProps extends HTMLAttributes<HTMLDivElement> {}

export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={twMerge('p-4', className)} {...props} />
  )
);

CardContent.displayName = 'CardContent';

export interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {}

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={twMerge('px-4 py-3 border-t border-primary/10', className)}
      {...props}
    />
  )
);

CardFooter.displayName = 'CardFooter';

export default Card;
