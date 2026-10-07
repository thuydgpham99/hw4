import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

/** Top nav. The right-hand side swaps between signed-out and signed-in states. */
export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? 'nav-link active' : 'nav-link'

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <nav className="nav">
      <div className="nav-inner">
        <NavLink to="/" className="nav-brand">
          <span className="nav-brand-name">Campus Customs</span>
          <span className="nav-brand-tag">New Haven, CT</span>
        </NavLink>

        <div className="nav-links">
          <NavLink to="/" className={linkClass} end>
            Home
          </NavLink>
          <NavLink to="/products" className={linkClass}>
            Products
          </NavLink>
          <NavLink to="/about" className={linkClass}>
            About Us
          </NavLink>

          {user ? (
            <>
              <span className="nav-greeting">
                Hi, {user.first_name || user.name.split(' ')[0]}
              </span>
              <button className="nav-link nav-logout" onClick={handleLogout}>
                Log Out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={linkClass}>
                Log In
              </NavLink>
              <NavLink
                to="/create-account"
                className={({ isActive }) =>
                  isActive ? 'nav-link nav-link-cta active' : 'nav-link nav-link-cta'
                }
              >
                Create Account
              </NavLink>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
