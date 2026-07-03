import { useEffect, useState } from 'react'
import type { Purpose, Strength, Reliant, StoneSize } from '../../api/types'
import {
  getPurposes, getStrengths, getReliants, getStoneSizes,
  createPurpose, updatePurposeMapping, deletePurpose,
  createStrength, updateStrength, deleteStrength,
  createReliant, deleteReliant,
  createStoneSize, deleteStoneSize,
} from '../../api/lookups'
import { extractErrorMessage } from '../../api/client'

// ניהול טבלאות העזר + מיפוי מטרה->מפרט (מזין את מנוע OD-2) + sort_order לחוזק.
export function LookupsPage() {
  const [purposes, setPurposes] = useState<Purpose[]>([])
  const [strengths, setStrengths] = useState<Strength[]>([])
  const [reliants, setReliants] = useState<Reliant[]>([])
  const [stones, setStones] = useState<StoneSize[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  // שדות "הוספה"
  const [newPurpose, setNewPurpose] = useState('')
  const [newStrength, setNewStrength] = useState('')
  const [newStrengthOrder, setNewStrengthOrder] = useState('')
  const [newReliant, setNewReliant] = useState('')
  const [newStone, setNewStone] = useState('')

  function reload() {
    Promise.all([getPurposes(), getStrengths(), getReliants(), getStoneSizes()])
      .then(([p, s, r, so]) => {
        setPurposes(p)
        setStrengths(s)
        setReliants(r)
        setStones(so)
      })
      .catch((e) => setError(extractErrorMessage(e)))
  }

  useEffect(reload, [])

  async function run(fn: () => Promise<unknown>) {
    setBusy(true)
    setError('')
    try {
      await fn()
      reload()
    } catch (e) {
      setError(extractErrorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  function setPurposeField(id: number, field: keyof Purpose, value: number | null) {
    setPurposes((prev) => prev.map((p) => (p.id === id ? { ...p, [field]: value } : p)))
  }

  const numOrNull = (v: string): number | null => (v === '' ? null : Number(v))

  return (
    <div>
      <div className="page-head">
        <h1>ניהול טבלאות עזר</h1>
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      {/* ===== מטרות + מיפוי מטרה->מפרט ===== */}
      <div className="card">
        <h2>מטרות ומיפוי מפרט</h2>
        <p className="muted">המיפוי (חוזק/סומך/גודל-אבן) קובע לאילו פניות מטרה מתאימה (OD-2).</p>
        <table className="admin-table">
          <thead>
            <tr><th>מטרה</th><th>חוזק נדרש</th><th>סומך נדרש</th><th>גודל-אבן נדרש</th><th></th></tr>
          </thead>
          <tbody>
            {purposes.map((p) => (
              <tr key={p.id}>
                <td>{p.Purpose}</td>
                <td>
                  <select value={p.req_strength_id ?? ''} onChange={(e) => setPurposeField(p.id, 'req_strength_id', numOrNull(e.target.value))}>
                    <option value="">— ללא —</option>
                    {strengths.map((s) => <option key={s.id} value={s.id}>{s.strength}</option>)}
                  </select>
                </td>
                <td>
                  <select value={p.req_reliant_id ?? ''} onChange={(e) => setPurposeField(p.id, 'req_reliant_id', numOrNull(e.target.value))}>
                    <option value="">— ללא —</option>
                    {reliants.map((r) => <option key={r.id} value={r.id}>{r.Reliant}</option>)}
                  </select>
                </td>
                <td>
                  <select value={p.req_stone_size_id ?? ''} onChange={(e) => setPurposeField(p.id, 'req_stone_size_id', numOrNull(e.target.value))}>
                    <option value="">— ללא —</option>
                    {stones.map((s) => <option key={s.id} value={s.id}>{s.Stone_size}</option>)}
                  </select>
                </td>
                <td className="row-actions">
                  <button type="button" className="btn btn-primary" disabled={busy}
                    onClick={() => run(() => updatePurposeMapping(p.id, {
                      req_strength_id: p.req_strength_id ?? null,
                      req_reliant_id: p.req_reliant_id ?? null,
                      req_stone_size_id: p.req_stone_size_id ?? null,
                    }))}>שמירת מיפוי</button>
                  <button type="button" className="btn btn-ghost" disabled={busy}
                    onClick={() => run(() => deletePurpose(p.id))}>מחיקה</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="inline-add">
          <input value={newPurpose} onChange={(e) => setNewPurpose(e.target.value)} placeholder="מטרה חדשה" />
          <button type="button" className="btn" disabled={busy || !newPurpose}
            onClick={() => run(async () => { await createPurpose({ Purpose: newPurpose }); setNewPurpose('') })}>הוספת מטרה</button>
        </div>
      </div>

      {/* ===== חוזק (עם sort_order) ===== */}
      <div className="card">
        <h2>חוזק</h2>
        <table className="admin-table">
          <thead><tr><th>חוזק</th><th>דירוג (sort)</th><th></th></tr></thead>
          <tbody>
            {strengths.map((s) => (
              <tr key={s.id}>
                <td>{s.strength}</td>
                <td>
                  <input type="number" style={{ width: '5rem' }} value={s.sort_order ?? ''}
                    onChange={(e) => setStrengths((prev) => prev.map((x) => x.id === s.id ? { ...x, sort_order: numOrNull(e.target.value) } : x))} />
                </td>
                <td className="row-actions">
                  <button type="button" className="btn btn-primary" disabled={busy}
                    onClick={() => run(() => updateStrength(s.id, { sort_order: s.sort_order ?? null }))}>שמירה</button>
                  <button type="button" className="btn btn-ghost" disabled={busy}
                    onClick={() => run(() => deleteStrength(s.id))}>מחיקה</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="inline-add">
          <input value={newStrength} onChange={(e) => setNewStrength(e.target.value)} placeholder="חוזק חדש (למשל ב-60)" />
          <input type="number" style={{ width: '5rem' }} value={newStrengthOrder} onChange={(e) => setNewStrengthOrder(e.target.value)} placeholder="דירוג" />
          <button type="button" className="btn" disabled={busy || !newStrength}
            onClick={() => run(async () => { await createStrength({ strength: newStrength, sort_order: numOrNull(newStrengthOrder) }); setNewStrength(''); setNewStrengthOrder('') })}>הוספה</button>
        </div>
      </div>

      {/* ===== סומך ===== */}
      <div className="card">
        <h2>סומך</h2>
        <div className="chip-list">
          {reliants.map((r) => (
            <span key={r.id} className="chip">
              {r.Reliant}
              <button type="button" className="chip-x" disabled={busy} onClick={() => run(() => deleteReliant(r.id))}>×</button>
            </span>
          ))}
        </div>
        <div className="inline-add">
          <input value={newReliant} onChange={(e) => setNewReliant(e.target.value)} placeholder="סומך חדש" />
          <button type="button" className="btn" disabled={busy || !newReliant}
            onClick={() => run(async () => { await createReliant({ Reliant: newReliant }); setNewReliant('') })}>הוספה</button>
        </div>
      </div>

      {/* ===== גודל אבן ===== */}
      <div className="card">
        <h2>גודל אבן</h2>
        <div className="chip-list">
          {stones.map((s) => (
            <span key={s.id} className="chip">
              {s.Stone_size}
              <button type="button" className="chip-x" disabled={busy} onClick={() => run(() => deleteStoneSize(s.id))}>×</button>
            </span>
          ))}
        </div>
        <div className="inline-add">
          <input value={newStone} onChange={(e) => setNewStone(e.target.value)} placeholder="גודל אבן חדש" />
          <button type="button" className="btn" disabled={busy || !newStone}
            onClick={() => run(async () => { await createStoneSize({ Stone_size: newStone }); setNewStone('') })}>הוספה</button>
        </div>
      </div>
    </div>
  )
}
