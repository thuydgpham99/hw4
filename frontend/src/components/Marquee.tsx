/** Scrolling band of store facts under the nav.
 *
 * The digital equivalent of painted lettering across a campus shop window — it
 * carries the things a storefront says without a shopper having to go looking:
 * where we are, that we're licensed, what the sizes run.
 */

const ITEMS = [
  'Officially Licensed Yale Merchandise',
  '57 Broadway · New Haven, CT',
  'Sizes XS – XXL',
  'Live Stock Counts On Every Page',
  'Open Late On Game Days',
  'Ask Our Shop Assistant Anything',
]

export default function Marquee() {
  // Rendered twice so the -50% translate loops seamlessly.
  const track = [...ITEMS, ...ITEMS]

  return (
    <div className="marquee" aria-hidden="true">
      <div className="marquee-track">
        {track.map((item, i) => (
          <span className="marquee-item" key={i}>
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}
