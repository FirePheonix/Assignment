import CTA from "@/sections/cta";
import FAQ from "@/sections/faq";
import Features1 from "@/sections/features-1";
import Features2 from "@/sections/features-2";
import Features3 from "@/sections/features-3";
import Features4 from "@/sections/features-4";
import Features5 from "@/sections/features-5";
import Footer from "@/sections/footer";
import { HeroSection2 } from "@/sections/hero-section";
import Pricing from "@/sections/pricing";
import Testimonials from "@/sections/testimonials";
import NavbarWrapper from "@/components/navbar-wrapper";
import ScrollToTop from "@/components/scroll-to-top";

export default function HomePage() {
  return (
    <>
      <ScrollToTop />
      <NavbarWrapper />
      <HeroSection2 />
      <div className="px-4 xl:px-0 max-w-5xl mx-auto space-y-20 sm:space-y-24 md:space-y-32 lg:space-y-40 scroll-smooth">
        <Features1 />
        <Features2 />
        <Features3 />
        <Features4 />
        <Features5 />
        <Testimonials />
        <Pricing />
        <FAQ />
        <CTA />
        <Footer />
      </div>
    </>
  )
}