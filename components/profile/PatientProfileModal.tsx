'use client';

import { useState, useEffect } from 'react';
import { Info, MapPin, AlertCircle } from 'lucide-react';
import type { PatientProfile } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { cn } from '@/lib/utils';
import { formatINRShort } from '@/lib/formatters';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface PatientProfileModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  profile: PatientProfile | null;
  onSave: (profile: PatientProfile) => void;
  onClear: () => void;
  onSearch?: (query: string) => void;
  lastQuery?: string;
}

const comorbidityOptions = [
  'Diabetes',
  'Hypertension',
  'Cardiac History',
  'Renal Disease',
  'None',
];

const genderOptions = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
] as const;

const suggestedLocations = [
  'Nagpur',
  'Mumbai',
  'Delhi',
  'Bangalore',
  'Raipur',
  'Bhopal',
  'Indore',
  'Nashik',
  'Aurangabad',
  'Surat',
];

const MAX_BUDGET = 2000000;

export function PatientProfileModal({
  open,
  onOpenChange,
  profile,
  onSave,
  onClear,
  onSearch,
  lastQuery,
}: PatientProfileModalProps) {
  // Local state for form fields
  const [age, setAge] = useState<number | null>(null);
  const [gender, setGender] = useState<PatientProfile['gender']>(null);
  const [comorbidities, setComorbidities] = useState<string[]>([]);
  const [budgetRange, setBudgetRange] = useState<[number, number]>([0, MAX_BUDGET]);
  const [location, setLocation] = useState('');
  const [errors, setErrors] = useState<{ age?: string; budget?: string; location?: string }>({});

  // Reset form when modal opens with current profile values
  useEffect(() => {
    if (open) {
      setAge(profile?.age ?? null);
      setGender(profile?.gender ?? null);
      setComorbidities(profile?.comorbidities ?? []);
      setBudgetRange([
        profile?.budget_min ?? 0,
        profile?.budget_max ?? MAX_BUDGET,
      ]);
      setLocation(profile?.location ?? '');
      setErrors({});
    }
  }, [open, profile]);

  const validateForm = (): boolean => {
    const newErrors: { age?: string; budget?: string; location?: string } = {};

    // Age validation
    if (age !== null && (age < 1 || age > 120)) {
      newErrors.age = 'Age must be between 1 and 120';
    }

    // Budget validation
    if (budgetRange[0] > budgetRange[1]) {
      newErrors.budget = 'Minimum budget cannot exceed maximum';
    }

    // Location validation (optional but if provided, should be non-empty)
    if (location.trim().length > 0 && location.trim().length < 2) {
      newErrors.location = 'Location must be at least 2 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleComorbidityToggle = (condition: string) => {
    if (condition === 'None') {
      setComorbidities(comorbidities.includes('None') ? [] : ['None']);
      return;
    }
    
    const filtered = comorbidities.filter((c) => c !== 'None');
    if (filtered.includes(condition)) {
      setComorbidities(filtered.filter((c) => c !== condition));
    } else {
      setComorbidities([...filtered, condition]);
    }
  };

  const handleBudgetChange = (value: number[]) => {
    const [min, max] = value as [number, number];
    // Ensure min doesn't exceed max
    if (min <= max) {
      setBudgetRange([min, max]);
      if (errors.budget) {
        setErrors((prev) => ({ ...prev, budget: undefined }));
      }
    }
  };

  const handleAgeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value === '') {
      setAge(null);
      setErrors((prev) => ({ ...prev, age: undefined }));
    } else {
      const parsed = parseInt(value, 10);
      if (!isNaN(parsed)) {
        setAge(parsed);
        if (parsed >= 1 && parsed <= 120) {
          setErrors((prev) => ({ ...prev, age: undefined }));
        }
      }
    }
  };

  const handleLocationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocation(e.target.value);
    if (errors.location && e.target.value.trim().length >= 2) {
      setErrors((prev) => ({ ...prev, location: undefined }));
    }
  };

  const handleLocationSelect = (loc: string) => {
    setLocation(loc);
    setErrors((prev) => ({ ...prev, location: undefined }));
  };

  const handleSave = () => {
    if (!validateForm()) {
      return;
    }

    onSave({
      age,
      gender,
      comorbidities: comorbidities.filter((c) => c !== 'None'),
      budget_min: budgetRange[0],
      budget_max: budgetRange[1],
      location: location.trim(),
    });
    onOpenChange(false);

    // Auto-trigger search if there's a previous query
    if (onSearch && lastQuery && lastQuery.trim()) {
      // Small delay to let modal close first
      setTimeout(() => {
        onSearch(lastQuery);
      }, 300);
    }
  };

  const handleClear = () => {
    setAge(null);
    setGender(null);
    setComorbidities([]);
    setBudgetRange([0, MAX_BUDGET]);
    setLocation('');
    setErrors({});
    onClear();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Patient Profile</DialogTitle>
          <DialogDescription>
            Optional context to improve estimate accuracy and provider relevance.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Location */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="location" className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-primary" />
                Location
              </Label>
              <HelpText>Find hospitals near your location.</HelpText>
            </div>
            <Input
              id="location"
              type="text"
              placeholder="Enter your city (e.g., Nagpur)"
              value={location}
              onChange={handleLocationChange}
              className={cn(errors.location && 'border-destructive')}
            />
            {errors.location && (
              <p className="text-xs text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {errors.location}
              </p>
            )}
            {/* Suggested locations */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {suggestedLocations.slice(0, 5).map((loc) => (
                <button
                  key={loc}
                  type="button"
                  onClick={() => handleLocationSelect(loc)}
                  className={cn(
                    'px-2.5 py-1 rounded-full text-xs font-medium transition-colors',
                    location === loc
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80'
                  )}
                >
                  {loc}
                </button>
              ))}
            </div>
          </div>

          {/* Age */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="age">Age</Label>
              <HelpText>Age affects procedure risk and recovery time estimates.</HelpText>
            </div>
            <Input
              id="age"
              type="number"
              min={1}
              max={120}
              placeholder="Enter age"
              value={age ?? ''}
              onChange={handleAgeChange}
              className={cn(errors.age && 'border-destructive')}
            />
            {errors.age && (
              <p className="text-xs text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {errors.age}
              </p>
            )}
          </div>

          {/* Gender */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Gender</Label>
              <HelpText>Some procedures have different considerations by gender.</HelpText>
            </div>
            <div className="flex flex-wrap gap-2">
              {genderOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setGender(option.value)}
                  className={cn(
                    'px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
                    gender === option.value
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Comorbidities */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Known Conditions</Label>
              <HelpText>Pre-existing conditions may increase costs and risks.</HelpText>
            </div>
            <div className="flex flex-wrap gap-2">
              {comorbidityOptions.map((condition) => (
                <button
                  key={condition}
                  type="button"
                  onClick={() => handleComorbidityToggle(condition)}
                  className={cn(
                    'px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
                    comorbidities.includes(condition)
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  )}
                >
                  {condition}
                </button>
              ))}
            </div>
          </div>

          {/* Budget */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Budget Range</Label>
              <HelpText>Filter results by your budget range.</HelpText>
            </div>
            <Slider
              value={budgetRange}
              onValueChange={handleBudgetChange}
              min={0}
              max={MAX_BUDGET}
              step={50000}
              className="w-full"
            />
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span className="font-mono">{formatINRShort(budgetRange[0])}</span>
              <span className="font-mono">{formatINRShort(budgetRange[1])}</span>
            </div>
            {errors.budget && (
              <p className="text-xs text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {errors.budget}
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 pt-2">
          <Button variant="outline" onClick={handleClear} className="flex-1">
            Clear All
          </Button>
          <Button onClick={handleSave} className="flex-1">
            {lastQuery ? 'Save & Update Results' : 'Apply & Search'}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Why we ask this: profile context helps estimate variation. Your data stays in this session UI.
        </p>
      </DialogContent>
    </Dialog>
  );
}

function HelpText({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-xs text-muted-foreground flex items-center gap-1">
      <Info className="h-3 w-3" />
      <span className="hidden sm:inline">{children}</span>
    </span>
  );
}
