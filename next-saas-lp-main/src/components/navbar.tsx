'use client'

import Logo from "./logo"
import Link from "next/link"
import { Button } from "./ui/button"
import { AlignJustify, X } from "lucide-react"
import { AnimatePresence } from 'motion/react'
import * as motion from "motion/react-m"
import { useState } from "react"
import ThemeSwitcher from "./theme-switcher"

const settings = {
  navLinks: [
    { name: 'home', href: '/' },
    { name: 'features', href: '#features' },
    { name: 'pricing', href: '#pricing' },
    { name: 'testimonials', href: '#testimonials' },
    { name: 'FAQ', href: '#faq' },
  ],
  cta: {
    content: 'try it for free',
    href: '/feed'
  }
}

export default function Navbar() {
  const [isOpen, setIsOpen] = useState<boolean>(false)

  const toggleMenu = () => {
    setIsOpen(!isOpen)
  }

  return (
    <nav className="w-full h-fit py-4 flex items-center justify-between">
      {/* Logo */}
      <Link href='/' title="Home" id="Logo">
        <Logo />
      </Link>

      {/* desktop menu */}
      <div className="items-center justify-center gap-5 hidden md:flex">

        {/* Nav Links */}
        <ul className="flex items-center justify-center gap-5 text-black dark:text-white font-medium select-none text-link">
          {settings.navLinks.map(link => (
            <li key={link.name}>
              <Link href={link.href} title={link.name} className="hover:opacity-80 transition-all capitalize">{link.name}</Link>
            </li>
          ))}
        </ul>

        {/* Theme Switcher */}
        <ThemeSwitcher />

        {/* Call To Action */}
        <Link href={settings.cta.href} title={settings.cta.content}>
          <Button className="capitalize">{settings.cta.content}</Button>
        </Link>
      </div>

      {/* mobile only - theme switcher and burger menu */}
      <div className="flex md:hidden items-center gap-2">
        <ThemeSwitcher />
        <motion.div
          initial={{ scale: 1, y: 0 }}
          whileTap={{ scale: 0.8 }}
          transition={{ duration: 0.3 }}
          className="bg-white dark:bg-black shadow-none flex cursor-pointer text-black dark:text-white"
          onClick={toggleMenu}
        >
          {!isOpen && <AlignJustify size={20} />}
          {isOpen && <X size={20} />}
        </motion.div>
      </div>

      {/* mobile only - menu container with AnimatePresence for exit animations */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 1, y: -20 }}
            animate={{ height: '100vh', opacity: 1, y: 0 }}
            exit={{ height: 0, opacity: 1, y: -20 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="fixed flex flex-col md:hidden top-16 left-0 w-full bg-white dark:bg-black z-50 overflow-hidden"
          >
            <div className="flex flex-col p-6 space-y-6">
              <ul className="flex flex-col space-y-2 text-black dark:text-white font-medium select-none text-base">
                {settings.navLinks.map(link => (
                  <li key={link.name}>
                    <Link href={link.href} title={link.name} onClick={toggleMenu} className="block py-2 capitalize">{link.name}</Link>
                  </li>
                ))}
              </ul>

              <Link href={settings.cta.href} title={settings.cta.content} onClick={toggleMenu}>
                <Button className="w-full capitalize">{settings.cta.content}</Button>
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}