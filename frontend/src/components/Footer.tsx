/** Site footer: store details and licensing, mirroring a campus-store layout. */
export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div>
          <h4>Campus Customs</h4>
          <p>57 Broadway</p>
          <p>New Haven, CT 06511</p>
          <p className="footer-licensed">Officially Licensed Yale Merchandise</p>
        </div>
        <div>
          <h4>Store Hours</h4>
          <p>Monday – Saturday, 10am – 7pm</p>
          <p>Sunday, 12pm – 5pm</p>
          <p>Extended hours on game days</p>
        </div>
        <div>
          <h4>Questions?</h4>
          <p>Our shop assistant is open all night,</p>
          <p>even when the store isn't.</p>
          <p>Look for the chat button, bottom right.</p>
        </div>
      </div>
    </footer>
  )
}
