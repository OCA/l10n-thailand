This module add following features to Purchase Request document, aimed to follow Thai Government procurement regulation.

1. Add following data to Purchase Request
    1.1 Procurement Type (ประเภท)
         - ซื้อ/จ้าง/เช่า
         - จ้างที่ปรึกษา
         - จ้างออกแบบและควบคุมงานก่อสร้าง
    1.2 Purchase Type (ระเบียบ)
         - จัดซื้อจัดจ้างผ่านพัสดุ
         - วงเงินเล็กน้อย
         - 79(2)
         - ว.119
    1.3 Procurement Method (วิธีการ)
         - เฉพาะเจาะจง
         - E-bidding
         - คัดเลือก
         - ประกาศเชิญชวนทั่วไป

2. Use substate to add an extra step, to verify document before approved
    The states of normal purchase request is,
       * Draft > To Approve > Approved

    Now changed to
       * Draft > To Approve (To Verify) > To Approve (Verified) > Approved

3. Add/edit following user fields to keep tracks of who is doing what
    * Prepared By (create_uid)
    * Requested By (requested_by)
    * Purchase Representative (assigned_to)
    * Verified By (verified_by)
    * Approved By (approved_by)

4. Add new Committee tab for both Procurement (ตณะกรรมการจัดซื้อจัดจ้าง) and Work Acceptance (คณะกรรมการการตรวจรับ)

5. Check exception logics when sent to approve
    The exception logic are based on Thai Government procurement regulation year 2560, in summary,
         * จ้างที่ปรึกษา ต้องมีกรรมการจัดซื้อจัดจ้างอย่างน้อย 5 คน และกรรมการตรวจรับอย่างน้อย 5 คน
         * จ้างออกแบบและควบคุมงานก่อสร้าง ต้องมีกรรมการจัดซื้อจัดจ้างอย่างน้อย 3 คน และกรรมการตรวจรับอย่างน้อย 3 คน
         * ระเบียบ วงเงินเล็กน้อย ไม่เกิน 100,000 บาท และต้องมีกรรมการตรวจรับอย่างน้อย 1 คน
         * ระเบียบ 79(2) ไม่เกิน 500,000 บาท
         * ระเบียบ ว.119 ไม่เกิน 10,000 บาท และต้องมีกรรมการตรวจรับอย่างน้อย 1 คน
         * ซื้อ/จ้าง/เช่า ไม่เกิน 500,000 บาท ต้องมีกรรมการตรวจรับอย่างน้อย 3 คน
         * ซื้อ/จ้าง/เช่า เกิน 500,000 บาท ต้องมีกรรมการจัดซื้อจัดจ้างอย่างน้อย 3 คน และกรรมการตรวจรับอย่างน้อย 3 คน
