import { useEffect, useMemo, useState } from 'react'
import type { ConcreteType, Purpose, Strength, Reliant, StoneSize } from '../../api/types'
import {
  getConcreteTypes, getPurposes, getStrengths, getReliants, getStoneSizes,
  createConcreteType, deleteConcreteType,
} from '../../api/lookups'
import { extractErrorMessage } from '../../api/client'

function toMap<T extends { id: number }>(items: T[], pick: (t: T) => string | null | undefined) {
  const m = new Map<number, string>()
  for (const it of items) {
    const v = pick(it)
    if (v) m.set(it.id, v)
  }
  return m
}

// ניהול סוגי בטון — הרכבת צירוף מטרה/חוזק/סומך/גודל-אבן.
export function ConcreteTypesPage() {
  const [types, setTypes] = useState<ConcreteType[]>([])
  const [purposes, setPurposes] = useState<Purpose[]>([])
  const [strengths, setStrengths] = useState<Strength[]>([])
  const [reliants, setReliants] = useState<Reliant[]>([])
  const [stones, setStones] = useState<StoneSize[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const [purposeId, setPurposeId] = useState('')
  const [strengthId, setStrengthId] = useState('')
  const [reliantId, setReliantId] = useState('')
  const [stoneId, setStoneId] = useState('')

  function reload() {
    Promise.all([getConcreteTypes(), getPurposes(), getStrengths(), getReliants(), getStoneSizes()])
      .then(([ct, p, s, r, so]) => { setTypes(ct); setPurposes(p); setStrengths(s); setReliants(r); setStones(so) })
      .catch((e) => setError(extractErrorMessage(e)))
  }
  useEffect(reload, [])

  const maps = useMemo(() => ({
    p: toMap(purposes, (x) => x.Purpose),
    s: toMap(strengths, (x) => x.strength),
    r: toMap(reliants, (x) => x.Reliant),
    so: toMap(stones, (x) => x.Stone_size),
  }), [purposes, strengths, reliants, stones])

  function label(ct: ConcreteType): string {
    const parts = [
      ct.Purpose_id ? maps.p.get(ct.Purpose_id) : null,
      ct.strength_id ? maps.s.get(ct.strength_id) : null,
      ct.Reliant_id ? maps.r.get(ct.Reliant_id) : null,
      ct.Stone_size_id ? maps.so.get(ct.Stone_size_id) : null,
    ].filter(Boolean)
    return parts.length ? parts.join(' · ') : `סוג בטון #${ct.id}`
  }

  async function run(fn: () => Promise<unknown>) {
    setBusy(true); setError('')
    try { await fn(); reload() } catch (e) { setError(extractErrorMessage(e)) } finally { setBusy(false) }
  }

  const num = (v: string) => (v === '' ? null : Number(v))

  return (
    <div>
      <div className="page-head"><h1>ניהול סוגי בטון</h1></div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <h2>הוספת סוג בטון</h2>
        <div className="form-grid">
          <div className="form-row">
            <label>מטרה</label>
            <select value={purposeId} onChange={(e) => setPurposeId(e.target.value)}>
              <option value="">— ללא —</option>
              {purposes.map((p) => <option key={p.id} value={p.id}>{p.Purpose}</option>)}
            </select>
          </div>
          <div className="form-row">
            <label>חוזק</label>
            <select value={strengthId} onChange={(e) => setStrengthId(e.target.value)}>
              <option value="">— ללא —</option>
              {strengths.map((s) => <option key={s.id} value={s.id}>{s.strength}</option>)}
            </select>
          </div>
          <div className="form-row">
            <label>סומך</label>
            <select value={reliantId} onChange={(e) => setReliantId(e.target.value)}>
              <option value="">— ללא —</option>
              {reliants.map((r) => <option key={r.id} value={r.id}>{r.Reliant}</option>)}
            </select>
          </div>
          <div className="form-row">
            <label>גודל אבן</label>
            <select value={stoneId} onChange={(e) => setStoneId(e.target.value)}>
              <option value="">— ללא —</option>
              {stones.map((s) => <option key={s.id} value={s.id}>{s.Stone_size}</option>)}
            </select>
          </div>
        </div>
        <button type="button" className="btn btn-primary" disabled={busy}
          onClick={() => run(async () => {
            await createConcreteType({
              Purpose_id: num(purposeId), strength_id: num(strengthId),
              Reliant_id: num(reliantId), Stone_size_id: num(stoneId),
            })
            setPurposeId(''); setStrengthId(''); setReliantId(''); setStoneId('')
          })}>הוספה</button>
      </div>

      <div className="card">
        <h2>סוגי בטון קיימים ({types.length})</h2>
        <div className="list">
          {types.map((ct) => (
            <div key={ct.id} className="card list-row">
              <div><strong>#{ct.id}</strong> · {label(ct)}</div>
              <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => run(() => deleteConcreteType(ct.id))}>מחיקה</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
