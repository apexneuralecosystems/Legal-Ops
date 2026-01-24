# Legal Ops AI — User Journey Maps

**Version**: 2.0 | **Date**: 21 January 2026

---

## 1. End-to-End User Journey (Partner View)

This diagram shows the complete lifecycle of a Partner setting up their firm and managing a case.

```mermaid
journey
    title Partner's Journey: From Signup to Getting Paid
    section Onboarding
      Sign up & Create Firm: 5: Partner
      Invite Associate: 4: Partner
      Configure Billing Rates: 3: Partner
    section Matter Intake
      Create New Client: 5: Partner
      Open New Matter: 5: Partner
      Assign Associate Team: 4: Partner
    section Execution (Oversight)
      Monitor AI Usage (Dashboard): 4: Partner
      Review Associate's Work: 3: Partner
    section Billing & Closure
      Receive "Matter Closed" Alert: 5: Partner
      Review Pre-Bill: 4: Partner
      Approve & Issue Invoice: 5: Partner
      Receive Payment Notification: 5: Partner
```

---

## 2. End-to-End User Journey (Associate View)

This diagram shows the day-to-day workflow of an Associate lawyer using the AI tools.

```mermaid
journey
    title Associate's Journey: AI-Assisted Legal Work
    section Start
      Receive Invite Email: 5: Associate
      Join Organization: 5: Associate
      View Assigned Matters: 4: Associate
    section Research & Drafting
      Upload Evidence PDF: 5: Associate
      Run AI OCR Analysis: 5: AI Agent
      Chat with Document (Q&A): 4: Associate
      Generate Pleading Draft: 5: Associate
    section Refinement
      Edit AI Draft: 3: Associate
      Log Manual Time: 2: Associate
      Request Partner Review: 4: Associate
```

---

## 3. Detailed Process Flow (State Diagram)

A more technical view of the states a user moves through.

```mermaid
stateDiagram-v2
    [*] --> Unregistered

    state "Onboarding" as Onboard {
        Unregistered --> Sign_Up
        Sign_Up --> Create_Org: I am a Founder
        Sign_Up --> Join_Org: I have an Invite
        Create_Org --> Dashboard
        Join_Org --> Dashboard
    }

    state "Matter Management" as Work {
        Dashboard --> New_Matter
        New_Matter --> Upload_Docs
        Upload_Docs --> AI_Tools
        
        state "AI Tools" as AI {
            OCR_Analysis --> Legal_Research
            Legal_Research --> Draft_Generation
            Draft_Generation --> Document_Review
        }
        
        AI_Tools --> Time_Logging
    }

    state "Financials" as Money {
        Time_Logging --> Pre_Bill_Review
        Pre_Bill_Review --> Invoice_Generated
        Invoice_Generated --> Payment_Received
    }

    Dashboard --> Work
    Work --> Money
    Money --> [*]
```

