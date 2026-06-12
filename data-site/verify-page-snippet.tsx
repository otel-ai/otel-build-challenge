/**
 * Reference snippet for /verify page — merge into otel-hackathon-data-site.
 *
 * Expose dataset_revision from env and aggregates that match
 * scripts/compute_load_fingerprint.py in otel-build-challenge.
 */

const DATASET_REVISION = process.env.NEXT_PUBLIC_DATASET_REVISION ?? "unknown";

export function VerifySummary({ stats }: { stats: VerifyStats }) {
  return (
    <section data-testid="verify-summary">
      <h2>Load verification</h2>
      <dl>
        <dt>dataset_revision</dt>
        <dd data-revision>{DATASET_REVISION}</dd>

        <dt>reservations_hackathon rows</dt>
        <dd>{stats.reservationsHackathonRows}</dd>

        <dt>active_stay_rows</dt>
        <dd>{stats.activeStayRows}</dd>

        <dt>active_reservations</dt>
        <dd>{stats.activeReservations}</dd>

        <dt>active_room_nights</dt>
        <dd>{stats.activeRoomNights}</dd>

        <dt>active_room_revenue</dt>
        <dd>{stats.activeRoomRevenue}</dd>

        <dt>july_2025_total_revenue</dt>
        <dd>{stats.july2025TotalRevenue}</dd>

        <dt>cancelled_reservation_count</dt>
        <dd>{stats.cancelledReservationCount}</dd>

        <dt>reservation_stay_pair_sha256</dt>
        <dd data-fingerprint>{stats.reservationStayPairSha256}</dd>
      </dl>
      <p>
        Candidates compare these values to <code>etl/LOAD_PROOF.json</code> after
        running <code>scripts/compute_load_fingerprint.py</code>.
      </p>
    </section>
  );
}

export type VerifyStats = {
  reservationsHackathonRows: number;
  activeStayRows: number;
  activeReservations: number;
  activeRoomNights: number;
  activeRoomRevenue: string;
  july2025TotalRevenue: string;
  cancelledReservationCount: number;
  reservationStayPairSha256: string;
};
