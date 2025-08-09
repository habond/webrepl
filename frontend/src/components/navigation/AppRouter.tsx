import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from '@/App'
import { AdminPage } from '@/components/admin/AdminPage'

export const AppRouter = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </BrowserRouter>
  )
}