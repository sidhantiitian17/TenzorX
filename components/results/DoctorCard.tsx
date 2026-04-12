'use client';

import { useEffect, useMemo, useState } from 'react';
import { Calendar, CheckCircle2, Clock, Copy, ExternalLink, Star } from 'lucide-react';
import type { Doctor } from '@/types';
import { formatINRFull } from '@/lib/formatters';
import { useAppDispatch, useAppState } from '@/lib/context';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from '@/components/ui/drawer';

interface DoctorCardProps {
  doctor: Doctor;
  hospitalName: string;
  procedure?: string;
}

export function DoctorCard({ doctor, hospitalName, procedure = 'the selected procedure' }: DoctorCardProps) {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const requestId = useMemo(
    () => `${hospitalName.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${doctor.id}`,
    [doctor.id, hospitalName]
  );

  const activeRequest = useMemo(
    () => state.appointmentRequests.find((request) => request.id === requestId),
    [requestId, state.appointmentRequests]
  );

  const [copied, setCopied] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(activeRequest?.slot ?? doctor.available_slots?.[0] ?? null);
  const [patientName, setPatientName] = useState('');
  const [phone, setPhone] = useState('');
  const [notes, setNotes] = useState('');
  const [confirmed, setConfirmed] = useState(false);

  const availableSlots = useMemo(() => doctor.available_slots ?? [], [doctor.available_slots]);

  useEffect(() => {
    if (!activeRequest) {
      return;
    }
    setSelectedSlot(activeRequest.slot);
    setPatientName(activeRequest.patientName);
    setPhone(activeRequest.phone);
    setNotes(activeRequest.notes);
  }, [activeRequest]);

  const feeLabel = (() => {
    if (doctor.fee_min && doctor.fee_max) {
      return `${formatINRFull(doctor.fee_min)} - ${formatINRFull(doctor.fee_max)}`;
    }
    if (doctor.fee_min) {
      return `${formatINRFull(doctor.fee_min)}+`;
    }
    return 'Fee shared on request';
  })();

  const copyAppointmentBrief = async () => {
    const brief = [
      `Appointment Request`,
      `Doctor: ${doctor.name}`,
      `Specialization: ${doctor.specialization}`,
      `Hospital: ${hospitalName}`,
      `Procedure: ${procedure}`,
      `Preferred slot: ${selectedSlot ?? 'Select in booking flow'}`,
      `Patient: ${patientName || 'Name pending'}`,
      `Phone: ${phone || 'Phone pending'}`,
      notes ? `Notes: ${notes}` : '',
      `Consult fee range: ${feeLabel}`,
      `Expected wait: ${doctor.wait_time_days ? `~${doctor.wait_time_days} day(s)` : 'Confirm with hospital'}`,
    ].join('\n');

    await navigator.clipboard.writeText(brief);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const openExternal = (mode: 'book' | 'profile') => {
    if (!doctor.booking_url) {
      void copyAppointmentBrief();
      return;
    }

    const separator = doctor.booking_url.includes('?') ? '&' : '?';
    const url = `${doctor.booking_url}${separator}view=${mode}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const confirmAppointment = () => {
    if (!selectedSlot || !patientName || !phone) {
      return;
    }

    const timestamp = new Date().toISOString();
    dispatch({
      type: 'UPSERT_APPOINTMENT_REQUEST',
      payload: {
        id: requestId,
        doctorId: doctor.id,
        doctorName: doctor.name,
        doctorSpecialization: doctor.specialization,
        hospitalName,
        procedure,
        slot: selectedSlot,
        patientName,
        phone,
        notes,
        status: activeRequest?.status === 'confirmed' ? 'confirmed' : 'requested',
        createdAt: activeRequest?.createdAt ?? timestamp,
        updatedAt: timestamp,
      },
    });

    setConfirmed(true);
    setTimeout(() => setConfirmed(false), 1800);
  };

  const statusLabel =
    activeRequest?.status === 'confirmed'
      ? 'Confirmed'
      : activeRequest?.status === 'cancelled'
      ? 'Cancelled'
      : activeRequest?.status === 'requested'
      ? 'Requested'
      : null;

  const statusClass =
    activeRequest?.status === 'confirmed'
      ? 'bg-emerald-100 text-emerald-700'
      : activeRequest?.status === 'cancelled'
      ? 'bg-red-100 text-red-700'
      : 'bg-amber-100 text-amber-700';

  return (
    <>
      <div className="rounded-lg border border-border bg-card p-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-sm font-semibold text-foreground">{doctor.name}</p>
            <p className="text-xs text-muted-foreground">{doctor.specialization}</p>
          </div>
          {doctor.rating && (
            <Badge variant="secondary" className="gap-1">
              <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
              {doctor.rating.toFixed(1)}
            </Badge>
          )}
        </div>

        {statusLabel && (
          <div className="mt-2">
            <Badge className={statusClass}>{statusLabel}</Badge>
          </div>
        )}

        <div className="mt-2 grid gap-1.5 text-xs text-muted-foreground">
          <p>Qualification: {doctor.qualification ?? 'Specialist consultant'}</p>
          <p>Experience: {doctor.experience_years} years</p>
          <p>Consultation: {feeLabel}</p>
          <p className="inline-flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            {doctor.wait_time_days ? `Next slot ~${doctor.wait_time_days} day(s)` : 'Next slot timing on request'}
          </p>
        </div>

        {availableSlots.length > 0 && (
          <div className="mt-3">
            <p className="mb-1 text-xs font-medium text-foreground">Select slot</p>
            <div className="flex flex-wrap gap-1.5">
              {availableSlots.slice(0, 3).map((slot) => (
                <button
                  key={slot}
                  onClick={() => setSelectedSlot(slot)}
                  className={
                    selectedSlot === slot
                      ? 'rounded-full border border-primary bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-primary'
                      : 'rounded-full border border-border bg-background px-2.5 py-1 text-[11px] text-muted-foreground hover:text-foreground'
                  }
                >
                  {slot}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mt-3 flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={() => openExternal('profile')}>
            <ExternalLink className="mr-1 h-3.5 w-3.5" />
            View Profile
          </Button>
          <Button size="sm" onClick={() => setDrawerOpen(true)}>
            <Calendar className="mr-1 h-3.5 w-3.5" />
            {activeRequest ? 'Manage Request' : 'Book Appointment'}
          </Button>
          <Button size="sm" variant="ghost" onClick={() => void copyAppointmentBrief()}>
            <Copy className="mr-1 h-3.5 w-3.5" />
            {copied ? 'Copied' : 'Copy Brief'}
          </Button>
        </div>
      </div>

      <Drawer open={drawerOpen} onOpenChange={setDrawerOpen}>
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle>Book Appointment with {doctor.name}</DrawerTitle>
            <DrawerDescription>
              {doctor.specialization} at {hospitalName} for {procedure}
            </DrawerDescription>
          </DrawerHeader>

          <div className="space-y-4 px-4 pb-2">
            <div className="rounded-md border border-border bg-muted/20 p-3 text-xs text-muted-foreground">
              <p>Consultation: {feeLabel}</p>
              <p>Expected wait: {doctor.wait_time_days ? `~${doctor.wait_time_days} day(s)` : 'Confirm with hospital'}</p>
            </div>

            <div>
              <p className="mb-1 text-sm font-medium">Choose slot</p>
              <div className="flex flex-wrap gap-2">
                {availableSlots.length > 0 ? (
                  availableSlots.map((slot) => (
                    <button
                      key={slot}
                      onClick={() => setSelectedSlot(slot)}
                      className={
                        selectedSlot === slot
                          ? 'rounded-md border border-primary bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary'
                          : 'rounded-md border border-border bg-background px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground'
                      }
                    >
                      {slot}
                    </button>
                  ))
                ) : (
                  <p className="text-xs text-muted-foreground">Slots are updated by hospital coordinators.</p>
                )}
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-foreground">Patient name</label>
                <Input
                  value={patientName}
                  onChange={(event) => setPatientName(event.target.value)}
                  placeholder="Enter patient name"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-foreground">Phone number</label>
                <Input
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  placeholder="Enter phone number"
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-foreground">Notes for hospital</label>
              <Textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Share timing preferences, symptoms, or language support needs"
                className="min-h-24"
              />
            </div>

            {confirmed && (
              <div className="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
                <CheckCircle2 className="h-4 w-4" />
                Appointment request prepared for {selectedSlot ?? 'chosen slot'}.
              </div>
            )}

            {activeRequest && (
              <div className="rounded-md border border-border bg-muted/20 px-3 py-2 text-xs text-muted-foreground">
                Current status: <span className="font-medium text-foreground">{activeRequest.status}</span> · Updated {new Date(activeRequest.updatedAt).toLocaleString('en-IN')}
              </div>
            )}
          </div>

          <DrawerFooter>
            <div className="flex flex-wrap gap-2">
              <Button onClick={confirmAppointment} disabled={!selectedSlot || !patientName || !phone}>
                Confirm Request
              </Button>
              <Button variant="outline" onClick={() => void copyAppointmentBrief()}>
                Copy Request
              </Button>
              <Button variant="outline" onClick={() => openExternal('book')}>
                Open Hospital Link
              </Button>
              <DrawerClose asChild>
                <Button variant="ghost">Close</Button>
              </DrawerClose>
            </div>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  );
}
