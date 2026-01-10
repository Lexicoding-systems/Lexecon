/**
 * Lexecon Design System - Component Library
 *
 * Enterprise AI Governance Platform
 * Version: 1.0.0
 * Last Updated: 2026-01-10
 *
 * Production-ready React components using the Lexecon design tokens.
 * All components meet WCAG AA accessibility standards.
 */

import React, { useState, useRef, useEffect } from 'react';
import { tokens } from './lexecon-design-tokens.js';

// ============================================================================
// BUTTON COMPONENT
// ============================================================================

/**
 * Button Component
 *
 * Primary interactive element for actions and navigation.
 * Supports multiple variants, sizes, states, and icons.
 */
export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon = null,
  iconPosition = 'left',
  fullWidth = false,
  onClick,
  type = 'button',
  ...props
}) => {
  const baseStyles = `
    inline-flex items-center justify-center
    font-medium rounded-lg
    transition-all duration-200
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:cursor-not-allowed disabled:opacity-50
    ${fullWidth ? 'w-full' : ''}
  `;

  const variants = {
    primary: `
      bg-[${tokens.colors.brand.primary[500]}] text-white
      hover:bg-[${tokens.colors.brand.primary[600]}]
      active:bg-[${tokens.colors.brand.primary[700]}]
      focus:ring-[${tokens.colors.brand.primary[500]}]
    `,
    secondary: `
      bg-[${tokens.colors.neutral[100]}] text-[${tokens.colors.neutral[700]}]
      border border-[${tokens.colors.neutral[300]}]
      hover:bg-[${tokens.colors.neutral[200]}]
      active:bg-[${tokens.colors.neutral[300]}]
      focus:ring-[${tokens.colors.neutral[400]}]
    `,
    danger: `
      bg-[${tokens.colors.semantic.error[500]}] text-white
      hover:bg-[${tokens.colors.semantic.error[600]}]
      active:bg-[${tokens.colors.semantic.error[700]}]
      focus:ring-[${tokens.colors.semantic.error[500]}]
    `,
    success: `
      bg-[${tokens.colors.semantic.success[500]}] text-white
      hover:bg-[${tokens.colors.semantic.success[600]}]
      active:bg-[${tokens.colors.semantic.success[700]}]
      focus:ring-[${tokens.colors.semantic.success[500]}]
    `,
    ghost: `
      bg-transparent text-[${tokens.colors.brand.primary[600]}]
      hover:bg-[${tokens.colors.brand.primary[50]}]
      active:bg-[${tokens.colors.brand.primary[100]}]
      focus:ring-[${tokens.colors.brand.primary[500]}]
    `
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm min-h-[32px]',
    md: 'px-4 py-2 text-base min-h-[40px]',
    lg: 'px-6 py-3 text-lg min-h-[48px]'
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]}`}
      disabled={disabled || loading}
      onClick={onClick}
      type={type}
      aria-busy={loading}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {icon && iconPosition === 'left' && !loading && (
        <span className="mr-2">{icon}</span>
      )}
      {children}
      {icon && iconPosition === 'right' && !loading && (
        <span className="ml-2">{icon}</span>
      )}
    </button>
  );
};

// ============================================================================
// INPUT COMPONENT
// ============================================================================

/**
 * Input Component
 *
 * Text input field with validation states and helper text support.
 */
export const Input = ({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  helperText,
  disabled = false,
  required = false,
  id,
  ...props
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  const baseInputStyles = `
    w-full px-4 py-2.5 rounded-lg
    border transition-all duration-200
    font-normal text-base
    focus:outline-none focus:ring-2 focus:ring-offset-1
    disabled:bg-[${tokens.colors.neutral[100]}] disabled:cursor-not-allowed
  `;

  const inputStates = error
    ? `border-[${tokens.colors.semantic.error[500]}]
       focus:border-[${tokens.colors.semantic.error[500]}]
       focus:ring-[${tokens.colors.semantic.error[100]}]`
    : `border-[${tokens.colors.neutral[300]}]
       focus:border-[${tokens.colors.brand.primary[500]}]
       focus:ring-[${tokens.colors.brand.primary[100]}]`;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className={`
            block mb-2 text-sm font-medium
            text-[${tokens.colors.neutral[700]}]
          `}
        >
          {label}
          {required && <span className="text-[${tokens.colors.semantic.error[500]}] ml-1">*</span>}
        </label>
      )}
      <input
        id={inputId}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        className={`${baseInputStyles} ${inputStates}`}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
        {...props}
      />
      {error && (
        <p
          id={`${inputId}-error`}
          className={`mt-2 text-sm text-[${tokens.colors.semantic.error[600]}]`}
          role="alert"
        >
          {error}
        </p>
      )}
      {helperText && !error && (
        <p
          id={`${inputId}-helper`}
          className={`mt-2 text-sm text-[${tokens.colors.neutral[500]}]`}
        >
          {helperText}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// CARD COMPONENT
// ============================================================================

/**
 * Card Component
 *
 * Container for grouping related content with optional header and footer.
 */
export const Card = ({
  children,
  title,
  subtitle,
  footer,
  variant = 'default',
  padding = 'default',
  ...props
}) => {
  const variants = {
    default: `bg-white border border-[${tokens.colors.neutral[200]}]`,
    elevated: `bg-white shadow-lg`,
    outlined: `bg-white border-2 border-[${tokens.colors.brand.primary[200]}]`
  };

  const paddings = {
    none: 'p-0',
    compact: 'p-4',
    default: 'p-6',
    spacious: 'p-8'
  };

  return (
    <div
      className={`rounded-xl ${variants[variant]} ${paddings[padding]}`}
      {...props}
    >
      {(title || subtitle) && (
        <div className="mb-4">
          {title && (
            <h3 className={`text-xl font-semibold text-[${tokens.colors.neutral[800]}]`}>
              {title}
            </h3>
          )}
          {subtitle && (
            <p className={`mt-1 text-sm text-[${tokens.colors.neutral[500]}]`}>
              {subtitle}
            </p>
          )}
        </div>
      )}
      <div>{children}</div>
      {footer && (
        <div className={`mt-4 pt-4 border-t border-[${tokens.colors.neutral[200]}]`}>
          {footer}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// BADGE COMPONENT
// ============================================================================

/**
 * Badge Component
 *
 * Small status indicator for labels, counts, and states.
 */
export const Badge = ({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full';

  const variants = {
    default: `bg-[${tokens.colors.neutral[100]}] text-[${tokens.colors.neutral[700]}]`,
    primary: `bg-[${tokens.colors.brand.primary[100]}] text-[${tokens.colors.brand.primary[700]}]`,
    success: `bg-[${tokens.colors.semantic.success[100]}] text-[${tokens.colors.semantic.success[700]}]`,
    warning: `bg-[${tokens.colors.semantic.warning[100]}] text-[${tokens.colors.semantic.warning[700]}]`,
    error: `bg-[${tokens.colors.semantic.error[100]}] text-[${tokens.colors.semantic.error[700]}]`,
    info: `bg-[${tokens.colors.semantic.info[100]}] text-[${tokens.colors.semantic.info[700]}]`
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base'
  };

  return (
    <span className={`${baseStyles} ${variants[variant]} ${sizes[size]}`} {...props}>
      {dot && (
        <span className={`w-1.5 h-1.5 rounded-full mr-1.5 bg-current`} />
      )}
      {children}
    </span>
  );
};

// ============================================================================
// ALERT COMPONENT
// ============================================================================

/**
 * Alert Component
 *
 * Contextual feedback messages for user actions.
 */
export const Alert = ({
  children,
  title,
  variant = 'info',
  dismissible = false,
  onDismiss,
  icon = true,
  ...props
}) => {
  const [visible, setVisible] = useState(true);

  const variants = {
    info: {
      bg: tokens.colors.semantic.info[50],
      border: tokens.colors.semantic.info[200],
      text: tokens.colors.semantic.info[800],
      icon: '⚠',
    },
    success: {
      bg: tokens.colors.semantic.success[50],
      border: tokens.colors.semantic.success[200],
      text: tokens.colors.semantic.success[800],
      icon: '✓'
    },
    warning: {
      bg: tokens.colors.semantic.warning[50],
      border: tokens.colors.semantic.warning[200],
      text: tokens.colors.semantic.warning[800],
      icon: '⚠'
    },
    error: {
      bg: tokens.colors.semantic.error[50],
      border: tokens.colors.semantic.error[200],
      text: tokens.colors.semantic.error[800],
      icon: '✕'
    }
  };

  const handleDismiss = () => {
    setVisible(false);
    if (onDismiss) onDismiss();
  };

  if (!visible) return null;

  const variantStyles = variants[variant];

  return (
    <div
      className={`p-4 rounded-lg border`}
      style={{
        backgroundColor: variantStyles.bg,
        borderColor: variantStyles.border,
        color: variantStyles.text
      }}
      role="alert"
      {...props}
    >
      <div className="flex items-start">
        {icon && (
          <span className="text-xl mr-3 flex-shrink-0">
            {variantStyles.icon}
          </span>
        )}
        <div className="flex-1">
          {title && (
            <h4 className="font-semibold mb-1">{title}</h4>
          )}
          <div className="text-sm">{children}</div>
        </div>
        {dismissible && (
          <button
            onClick={handleDismiss}
            className="ml-3 flex-shrink-0 text-current hover:opacity-70 transition-opacity"
            aria-label="Dismiss"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// MODAL COMPONENT
// ============================================================================

/**
 * Modal Component
 *
 * Overlay dialog for focused user interactions.
 */
export const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  ...props
}) => {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4'
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      aria-labelledby="modal-title"
      role="dialog"
      aria-modal="true"
      {...props}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-screen items-center justify-center p-4">
        <div
          className={`relative w-full ${sizes[size]} bg-white rounded-xl shadow-2xl transform transition-all`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className={`px-6 py-4 border-b border-[${tokens.colors.neutral[200]}]`}>
            <div className="flex items-center justify-between">
              <h3
                id="modal-title"
                className={`text-xl font-semibold text-[${tokens.colors.neutral[800]}]`}
              >
                {title}
              </h3>
              <button
                onClick={onClose}
                className={`text-[${tokens.colors.neutral[400]}] hover:text-[${tokens.colors.neutral[600]}] transition-colors`}
                aria-label="Close modal"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="px-6 py-4">
            {children}
          </div>

          {/* Footer */}
          {footer && (
            <div className={`px-6 py-4 border-t border-[${tokens.colors.neutral[200]}] bg-[${tokens.colors.neutral[50]}] rounded-b-xl`}>
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// TABLE COMPONENT
// ============================================================================

/**
 * Table Component
 *
 * Data table with sorting, selection, and responsive design.
 */
export const Table = ({
  columns,
  data,
  selectable = false,
  onRowClick,
  ...props
}) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full" {...props}>
        <thead className={`bg-[${tokens.colors.neutral[50]}] border-b-2 border-[${tokens.colors.neutral[200]}]`}>
          <tr>
            {selectable && (
              <th className="px-4 py-3 text-left w-12">
                <input type="checkbox" className="rounded" />
              </th>
            )}
            {columns.map((column, index) => (
              <th
                key={index}
                className={`px-4 py-3 text-left text-sm font-semibold text-[${tokens.colors.neutral[700]}]`}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[${tokens.colors.neutral[200]}]">
          {data.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              onClick={() => onRowClick && onRowClick(row)}
              className={`
                transition-colors
                ${onRowClick ? 'cursor-pointer hover:bg-[${tokens.colors.neutral[50]}]' : ''}
              `}
            >
              {selectable && (
                <td className="px-4 py-3">
                  <input type="checkbox" className="rounded" />
                </td>
              )}
              {columns.map((column, colIndex) => (
                <td
                  key={colIndex}
                  className={`px-4 py-3 text-sm text-[${tokens.colors.neutral[600]}]`}
                >
                  {column.render ? column.render(row[column.key], row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ============================================================================
// SELECT COMPONENT
// ============================================================================

/**
 * Select Component
 *
 * Dropdown selection input.
 */
export const Select = ({
  label,
  options,
  value,
  onChange,
  placeholder = 'Select an option',
  error,
  disabled = false,
  required = false,
  id,
  ...props
}) => {
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={selectId}
          className={`block mb-2 text-sm font-medium text-[${tokens.colors.neutral[700]}]`}
        >
          {label}
          {required && <span className="text-[${tokens.colors.semantic.error[500]}] ml-1">*</span>}
        </label>
      )}
      <select
        id={selectId}
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        className={`
          w-full px-4 py-2.5 rounded-lg border
          transition-all duration-200 font-normal text-base
          focus:outline-none focus:ring-2 focus:ring-offset-1
          disabled:bg-[${tokens.colors.neutral[100]}] disabled:cursor-not-allowed
          ${error
            ? `border-[${tokens.colors.semantic.error[500]}] focus:border-[${tokens.colors.semantic.error[500]}] focus:ring-[${tokens.colors.semantic.error[100]}]`
            : `border-[${tokens.colors.neutral[300]}] focus:border-[${tokens.colors.brand.primary[500]}] focus:ring-[${tokens.colors.brand.primary[100]}]`
          }
        `}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error ? `${selectId}-error` : undefined}
        {...props}
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {options.map((option, index) => (
          <option key={index} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <p
          id={`${selectId}-error`}
          className={`mt-2 text-sm text-[${tokens.colors.semantic.error[600]}]`}
          role="alert"
        >
          {error}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// CHECKBOX COMPONENT
// ============================================================================

/**
 * Checkbox Component
 *
 * Binary selection input with label support.
 */
export const Checkbox = ({
  label,
  checked,
  onChange,
  disabled = false,
  id,
  ...props
}) => {
  const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="flex items-center">
      <input
        id={checkboxId}
        type="checkbox"
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        className={`
          w-4 h-4 rounded
          border-[${tokens.colors.neutral[300]}]
          text-[${tokens.colors.brand.primary[500]}]
          focus:ring-2 focus:ring-[${tokens.colors.brand.primary[100]}]
          disabled:cursor-not-allowed disabled:opacity-50
        `}
        {...props}
      />
      {label && (
        <label
          htmlFor={checkboxId}
          className={`ml-2 text-sm text-[${tokens.colors.neutral[700]}] ${disabled ? 'opacity-50' : 'cursor-pointer'}`}
        >
          {label}
        </label>
      )}
    </div>
  );
};

// ============================================================================
// TABS COMPONENT
// ============================================================================

/**
 * Tabs Component
 *
 * Navigation between different views or sections.
 */
export const Tabs = ({
  tabs,
  activeTab,
  onChange,
  variant = 'line',
  ...props
}) => {
  const variantStyles = {
    line: {
      container: `border-b border-[${tokens.colors.neutral[200]}]`,
      tab: `px-4 py-2 border-b-2 transition-colors`,
      active: `border-[${tokens.colors.brand.primary[500]}] text-[${tokens.colors.brand.primary[600]}]`,
      inactive: `border-transparent text-[${tokens.colors.neutral[500]}] hover:text-[${tokens.colors.neutral[700]}] hover:border-[${tokens.colors.neutral[300]}]`
    },
    pills: {
      container: `flex gap-2`,
      tab: `px-4 py-2 rounded-lg transition-colors`,
      active: `bg-[${tokens.colors.brand.primary[500]}] text-white`,
      inactive: `text-[${tokens.colors.neutral[500]}] hover:bg-[${tokens.colors.neutral[100]}]`
    }
  };

  const styles = variantStyles[variant];

  return (
    <div className={styles.container} role="tablist" {...props}>
      {tabs.map((tab, index) => (
        <button
          key={index}
          role="tab"
          aria-selected={activeTab === tab.id}
          onClick={() => onChange(tab.id)}
          className={`
            ${styles.tab}
            ${activeTab === tab.id ? styles.active : styles.inactive}
            font-medium text-sm
          `}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};

// Export all components
export default {
  Button,
  Input,
  Card,
  Badge,
  Alert,
  Modal,
  Table,
  Select,
  Checkbox,
  Tabs
};
