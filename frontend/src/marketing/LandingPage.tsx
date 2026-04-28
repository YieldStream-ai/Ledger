import { Nav } from './components/Nav'
import { Hero } from './components/Hero'
import { TrustBar } from './components/TrustBar'
import { FeaturesGrid } from './components/FeaturesGrid'
import { HowItWorks } from './components/HowItWorks'
import { TemplateCoverage } from './components/TemplateCoverage'
import { AccuracyMetrics } from './components/AccuracyMetrics'
import { ComparisonTable } from './components/ComparisonTable'
import { UseCases } from './components/UseCases'
import { Pricing } from './components/Pricing'
import { FinalCTA } from './components/FinalCTA'
import { Footer } from './components/Footer'

export function LandingPage() {
  return (
    <div className="min-h-screen bg-[var(--bg)]">
      <Nav />
      <main>
        <Hero />
        <TrustBar />
        <FeaturesGrid />
        <HowItWorks />
        <TemplateCoverage />
        <AccuracyMetrics />
        <ComparisonTable />
        <UseCases />
        <Pricing />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  )
}
