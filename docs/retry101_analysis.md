# retry-101 full-run analysis (rev2, patched pipeline)

Run: 101 Q, gen1 p50 15.4s, gen2 p50 21.7s, total GPU ~3462s. Outcomes: PASS_FIRST 8, PASS_RETRY 15, REFUSED_DOMAIN 16, FAIL_BOTH 62.

## 1. Transition vs v1 baseline (92 FAIL / 9 PASS)

| v1 | FAIL_BOTH | PASS_FIRST | PASS_RETRY | REFUSED_DOMAIN |
|---|---|---|---|---|
| FAIL | 61 | 1 | 14 | 16 |
| PASS | 1 | 7 | 1 | 0 |

v1-PASS now failing (nondeterminism watchlist): ['505']

## 2. HINT_KEYS parse check: n_hints matches computed hint count on 54/101 rows
  - id=609: csv n_hints=0 computed=4 u1=['InventoryEntry', 'InventoryEntryDetails', 'Vendor_Master', 'FeesCollection.Vendor_ID']
  - id=604: csv n_hints=0 computed=1 u1=['FixedAssetDetails', 'FixedAssetMaster', 'UserAccountRoleDetails.Branch_Id']
  - id=591: csv n_hints=0 computed=1 u1=['StaffVerificationMaster', 'UserAccountRoleDetails.Branch_Id']
  - id=589: csv n_hints=4 computed=3 u1=['LeaveEntryMaster.NetPay', 'LeaveEntryMaster.PaidAmount', 'UserAccountRoleDetails.Branch_Id']
  - id=587: csv n_hints=2 computed=1 u1=['Biometric_Attendance', 'UserAccountRoleDetails.Branch_Id']
  - id=579: csv n_hints=2 computed=1 u1=['UserAccountRoleDetails.Branch_Id']
  - id=573: csv n_hints=5 computed=1 u1=['Student_Master.ShiftName', 'UserAccountRoleDetails.Branch_Id']
  - id=572: csv n_hints=2 computed=1 u1=['Subject_Master.DepartmentName', 'UserAccountRoleDetails.Branch_Id']
  - id=569: csv n_hints=2 computed=1 u1=['UserAccountRoleDetails.Branch_Id']
  - id=546: csv n_hints=2 computed=1 u1=['Student_Master.AdharNo', 'Student_Master.UDISEPlus']
  - id=541: csv n_hints=2 computed=1 u1=['ClassMaster.MaxStrength']
  - id=534: csv n_hints=2 computed=1 u1=['ClassMaster.TotalSeats']
  - id=525: csv n_hints=4 computed=1 u1=['UserAccountRoleDetails.Branch_Id']
  - id=505: csv n_hints=1 computed=0 u1=['ClassMaster.TotalNoStudent']
  - id=499: csv n_hints=0 computed=2 u1=['Stock_Master', 'UserAccountRoleDetails.Branch_Id']
  - id=498: csv n_hints=0 computed=2 u1=['PurchaseOrderDetails', 'PurchaseOrderMaster', 'Vendor_Master', 'UserAccountRoleDetails.Branch_Id']
  - id=497: csv n_hints=0 computed=1 u1=['PurchaseOrderMaster', 'PurchaseOrderStatus', 'UserAccountRoleDetails.Branch_Id']
  - id=495: csv n_hints=0 computed=1 u1=['FurnitureMaster', 'UserAccountRoleDetails.Branch_Id']
  - id=493: csv n_hints=0 computed=1 u1=['BookIssueMaster', 'Book_Master', 'Branch_Master', 'UserAccountRoleDetails.Branch_Id']
  - id=492: csv n_hints=0 computed=1 u1=['ComputerMaster', 'UserAccountRoleDetails.Branch_Id']
  - id=491: csv n_hints=0 computed=1 u1=['SportsEquipment_Master', 'SportsEventEntryDetail', 'SportsEventEntryMaster', 'SportsEventMaster', 'UserAccountRoleDetails.Branch_Id']
  - id=484: csv n_hints=0 computed=1 u1=['LibraryBookMaster', 'UserAccountRoleDetails.Branch_Id']
  - id=460: csv n_hints=2 computed=1 u1=['EmployeeMaster.ContractExpiryDate']
  - id=432: csv n_hints=2 computed=1 u1=['StudentAttendance.Attendance_Staff_ID', 'UserAccountRoleDetails.Branch_Id']
  - id=426: csv n_hints=3 computed=2 u1=['StudentAttendance.InTime', 'UserAccountRoleDetails.Branch_Id']
  - id=412: csv n_hints=5 computed=2 u1=['StudentMarkDetails.MarksDate', 'UserAccountRoleDetails.Branch_Id']
  - id=410: csv n_hints=3 computed=0 u1=['Stream_Master', 'StudentMarkDetails.ClassName', 'StudentMarkMaster.StreamID']
  - id=408: csv n_hints=6 computed=2 u1=['StudentMarkDetails.Subject_ID', 'UserAccountRoleDetails.Branch_Id']
  - id=406: csv n_hints=4 computed=1 u1=['UserAccountRoleDetails.Branch_Id']
  - id=388: csv n_hints=5 computed=1 u1=['ExamConfigurationEvaluationDetails.SubjectID', 'Subject_Master.SubjectTypeID', 'UserAccountRoleDetails.Branch_Id']
  - id=382: csv n_hints=3 computed=1 u1=['StudentMarkMaster.IsDeleted', 'StudentMarkMaster.Student_ID', 'UserAccountRoleDetails.Branch_Id']
  - id=377: csv n_hints=3 computed=2 u1=['StudentMarkDetails.IsRepeating', 'UserAccountRoleDetails.Branch_Id']
  - id=376: csv n_hints=4 computed=2 u1=['StudentAcademicDetail.AttendancePercent', 'StudentMarkDetails.IsDeleted', 'StudentMarkDetails.SubjectID', 'UserAccountRoleDetails.Branch_Id']
  - id=375: csv n_hints=4 computed=0 u1=['StudentMarkMaster.SubjectName']
  - id=374: csv n_hints=5 computed=1 u1=['UserAccountRoleDetails.Branch_Id']
  - id=362: csv n_hints=5 computed=2 u1=['StudentMarkDetails.Subject_ID', 'StudentMarkMaster.TermName', 'UserAccountRoleDetails.Branch_Id']
  - id=361: csv n_hints=5 computed=2 u1=['StudentMarkDetails.Subject_ID', 'Subject_Master.StreamName', 'UserAccountRoleDetails.Branch_Id']
  - id=350: csv n_hints=3 computed=2 u1=['FeesCollection_Details.Branch_ID', 'FeesCollection_Details.WriteOff_Amt']
  - id=347: csv n_hints=2 computed=1 u1=['FeesCollection_Details.Amount']
  - id=342: csv n_hints=5 computed=2 u1=['FeesCollection_Details.ReminderNo', 'UserAccountRoleDetails.Branch_Id']
  - id=315: csv n_hints=5 computed=1 u1=['UserAccountRoleDetails.Branch_Id']
  - id=300: csv n_hints=5 computed=3 u1=['FeesCollection_Details.Student_ID', 'FeesInformationStudentDetail.Fees_Collection_ID', 'UserAccountRoleDetails.Branch_Id']
  - id=299: csv n_hints=2 computed=1 u1=['FeesCollection_Details.Branch_ID']
  - id=291: csv n_hints=2 computed=1 u1=['Fees_Master.IsTransportFee', 'UserAccountRoleDetails.Branch_Id']
  - id=289: csv n_hints=2 computed=1 u1=['FeesCollection.Gross_Amount', 'FeesCollection.Total_Amt', 'UserAccountRoleDetails.Branch_Id']
  - id=286: csv n_hints=4 computed=1 u1=['UserAccountRoleDetails.Branch_Id']
  - id=278: csv n_hints=5 computed=1 u1=['FeesCollection_Details.ExtraCharges', 'UserAccountRoleDetails.Branch_Id']

## 3. Hint efficacy on FAIL_BOTH (attempt-1 hinted identifiers: 87)
- fixed by retry (absent in attempt-2): 72  (83%)
- repeated despite hint:               15  (17%)

Top repeated-despite-hint:
   1x  InventoryItem_Master.ItemCategory_Name
   1x  Staff_Master.IsPOCSOCompleted
   1x  Staff_Master.IsPOSHCompleted
   1x  StudentAcademicDetail.TCNo
   1x  TCRequest.TC_No
   1x  ClassMaster.MaxStrength
   1x  StudentAcademicDetail.IsRTE
   1x  DriverFeedback
   1x  StudentAttendance.InTime
   1x  StudentMarkDetails.MarksDate
   1x  ProgressCardDataRetrieval.StaffName
   1x  FeesCollection_Details.ReminderNo

## 4. Attempt-2 unknowns across FAIL_BOTH: 105 hits, 95 distinct
by class: COL_HALLUC=86, TABLE_HALLUC=9
repeated-from-attempt-1: 40 hits | fresh (new hallucinations): 65 hits

## 5. v2.2 HINT worklist: 77 distinct unhinted attempt-2 identifiers

| ident | hits | class | schema verdict / closest real |
|---|---|---|---|
| StudentMarkDetails.ExamTypeID | 4 | COL_HALLUC | StudentMarkDetails.EvalHierID  |
| StudentMarkDetails.IsDeleted | 3 | COL_HALLUC | StudentMarkDetails.Deleted  |
| Staff_Master.DesignationID | 2 | COL_HALLUC | Staff_Master.Designation_ID/SpouseDesignation/Religion_ID  |
| FeesCollection_Details.IsDonation | 2 | COL_HALLUC | FeesCollection_Details (no similar col)  |
| InventoryType_Master | 1 | TABLE_HALLUC | InventoryItem_Master/InventorySupplierType_Master/InventorySupplierMaster  |
| InventoryItem_Master.InventoryTypeID | 1 | COL_HALLUC | InventoryItem_Master.Vendor_ID/ItemCategory_ID  |
| Fuel_Consumption_Details | 1 | TABLE_HALLUC | FeesCollection_Details/PaymentConfiguration_Details/FeesCollection_ModeDetails DA-family:fuel |
| ParentComplaint_Master | 1 | TABLE_HALLUC | Company_Master/Department_Master/BoardingPoint_Master DA-family:complaint |
| PerformanceAppraisal_Details | 1 | TABLE_HALLUC | Branch_Facility_Details/Branch_Academic_Details/ProgressCardClassDetails DA-family:appraisal |
| StaffDesignationMaster.DesignationName | 1 | COL_HALLUC | StaffDesignationMaster.Description  |
| GenerateSalaryEmployee_Master.PaidAmount | 1 | COL_HALLUC | GenerateSalaryEmployee_Master.GrossAmount  |
| Staff_Master.StaffDOJ | 1 | COL_HALLUC | Staff_Master.Staff_DOJ/Staff_DOB/Staff_ID  |
| SubjectAllocation_Master.ClassLevel | 1 | COL_HALLUC | SubjectAllocation_Master.IsClassTeacher/Class_ID  |
| ExamEvaluationDetails | 1 | TABLE_HALLUC | ExamConfigurationEvaluationDetails/OtherExamConfigurationEvaluationDetails/ExaminationPlanningDetails  |
| ProgressCardDataRetrieval.AcademicYearName | 1 | COL_HALLUC | ProgressCardDataRetrieval.AcademicYearID/TermName/ExamTypeName  |
| Student_Master.ShiftName | 1 | COL_HALLUC | Student_Master.StaffName/FirstName/SportsName  |
| EvaluationMaster.GradeEntryDate | 1 | COL_HALLUC | EvaluationMaster (no similar col)  |
| EvaluationMaster.TestDate | 1 | COL_HALLUC | EvaluationMaster.IsDeleted  |
| ProgressCardDataRetrieval.Subject_ID | 1 | COL_HALLUC | ProgressCardDataRetrieval.SubjectID/SubjectTypeID/ParentSubjectID  |
| LeaveEntryMaster.Student_ID | 1 | COL_HALLUC | LeaveEntryMaster.Staff_ID/StaffType_ID/LeaveStatus_ID  |
| StudentAttendance.SectionID | 1 | COL_HALLUC | StudentAttendance.Section_ID/Student_ID  |
| Student_Master.CommunicationPinCode | 1 | COL_HALLUC | Student_Master.CommunicationMobileNo/CommunicationMailID/CommunicationeMailID  |
| ApplicationEntry.AdmissionTypeName | 1 | COL_HALLUC | ApplicationEntry.AdmissionType_Name/AdmissionType_ID/AdmissionDate  |
| ApplicationEntry.Application_Mode | 1 | COL_HALLUC | ApplicationEntry.ApplicationNo/ApplicationDate/ApplicationRefNo  |
| ApplicationEntry.Student_ID | 1 | COL_HALLUC | ApplicationEntry.Student_ClassID/StudentImg/StudentDob  |
| ClassSectionMaster.Branch_Id | 1 | COL_HALLUC | ClassSectionMaster.BranchID/Class_Id  |
| StudentAcademicDetail.ClassSectionID | 1 | COL_HALLUC | StudentAcademicDetail.SectionID/ClassID/IsSectionChanged  |
| Concession_Master.ApprovalStatus | 1 | COL_HALLUC | Concession_Master (no similar col)  |
| RTE_Details | 1 | TABLE_HALLUC | Grade_Details/ClassDetails/Route_MasterDetails  |
| RTE_Master | 1 | TABLE_HALLUC | GSTMaster/Route_Master/UOM_Master  |
| Student_Master.CityName | 1 | COL_HALLUC | Student_Master.Community_Name/FirstName/LastName  |
| ClassMaster.TotalNoStudent | 1 | COL_HALLUC | ClassMaster (no similar col)  |
| InventoryItem_Master.Condition_Name | 1 | COL_HALLUC | InventoryItem_Master.Vendor_Name/ItemName  |
| InventoryItem_Master.ExpiryDate | 1 | COL_HALLUC | InventoryItem_Master.Updated_Date/Created_Date  |
| InventoryItem_Master.ReorderLevel | 1 | COL_HALLUC | InventoryItem_Master (no similar col)  |
| VehicleMaster.PUC_Date | 1 | COL_HALLUC | VehicleMaster.FC_Date/Updated_Date/Created_Date  |
| BoardingPoint_Master.DriverID | 1 | COL_HALLUC | BoardingPoint_Master (no similar col)  |
| FeedbackTicket.Route_ID | 1 | COL_HALLUC | FeedbackTicket.StudentID  |
| FeesCollection_Details.TransportFeeName | 1 | COL_HALLUC | FeesCollection_Details.LateFeeName/FeesType_Name/FeesGroup_Name  |
| Staff_Master.ContractEndDate | 1 | COL_HALLUC | Staff_Master.Created_Date/ServiceConfirmationDate/Com_State  |
| Staff_Master.IsHold | 1 | COL_HALLUC | Staff_Master.IsDeleted/BEdHolder  |
| StaffQualificationMaster | 1 | TABLE_HALLUC | StaffEvaluationMaster/StaffDesignationMaster/StaffRatingMaster  |
| Staff_Master.ID | 1 | COL_HALLUC | Staff_Master.TypeID  |
| StudentAttendance.InformParent | 1 | COL_HALLUC | StudentAttendance (no similar col)  |
| StudentAttendance.Attendance_Staff_ID | 1 | COL_HALLUC | StudentAttendance.Attendance_Status_ID/Attendance_Date/Attendance_Reason  |
| StudentMarkDetails.SubjectTypeID | 1 | COL_HALLUC | StudentMarkDetails.StudentID  |
| Student_Master.AcademicYearID | 1 | COL_HALLUC | Student_Master.AdmissionCategoryID/CanditateID/AdmissionType_ID  |
| Student_Master.ClassName | 1 | COL_HALLUC | Student_Master.LastName/BankName/ClassLastStudied  |
| Student_Master.StreamName | 1 | COL_HALLUC | Student_Master.Stream/StaffName/StreamID  |
| StudentMarkMaster.SubjectID | 1 | COL_HALLUC | StudentMarkMaster.SectionID/ExamSettingID  |
| ProgressCardDataRetrieval.Student_ID | 1 | COL_HALLUC | ProgressCardDataRetrieval.StudentID/StudentName/SubjectID  |
| Student_Master.Staff_FirstName | 1 | COL_HALLUC | Student_Master.StaffName/FirstName/LastName  |
| Student_Master.Staff_LastName | 1 | COL_HALLUC | Student_Master.StaffName/LastName/MotherLastName  |
| StudentMarkMaster.IsDeleted | 1 | COL_HALLUC | StudentMarkMaster.Deleted  |
| ExamConfigurationEvaluationDetails.EvalHierID | 1 | COL_HALLUC | ExamConfigurationEvaluationDetails.ExamHeaderID/EvaluationTypeID/SubjectEvaluationID  |
| StudentMarkMaster.SubjectName | 1 | COL_HALLUC | StudentMarkMaster (no similar col)  |
| StudentMarkDetails.SubjectName | 1 | COL_HALLUC | StudentMarkDetails (no similar col)  |
| ExamConfigurationEvaluationDetails.SubjectID | 1 | COL_HALLUC | ExamConfigurationEvaluationDetails.SubjectEvaluationID/ParentID/SubjectEvaluationName  |
| StudentMarkDetails.ClassID | 1 | COL_HALLUC | StudentMarkDetails (no similar col)  |
| Subject_Master.StreamName | 1 | COL_HALLUC | Subject_Master.Name/SubShortName  |
| StudentMarkMaster.MinMark | 1 | COL_HALLUC | StudentMarkMaster (no similar col)  |
| FeesCollection.Branch_Id | 1 | COL_HALLUC | FeesCollection.BranchID/Branch/Bank  |
| FeesCollection_Details.Part_Id | 1 | COL_HALLUC | FeesCollection_Details (no similar col)  |
| Student_Master.RemainingSecurityDeposit | 1 | COL_HALLUC | Student_Master.Security_Deposit_Date/Security_Deposit_Amount  |
| Student_Master.SecurityDepositAmount | 1 | COL_HALLUC | Student_Master.Security_Deposit_Amount/Security_Deposit_Date/Lumpsum_Amount  |
| BusFeeStrucure.IsDonation | 1 | COL_HALLUC | BusFeeStrucure (no similar col)  |
| BusFeeStrucure.IsIncludedInLumpSum | 1 | COL_HALLUC | BusFeeStrucure (no similar col)  |
| BusFeeStrucure.Lien_Amount | 1 | COL_HALLUC | BusFeeStrucure.Amount  |
| BusFeeStrucure.Paid_Amt | 1 | COL_HALLUC | BusFeeStrucure (no similar col)  |
| FeesCollection_Details.IsDeleted | 1 | COL_HALLUC | FeesCollection_Details (no similar col)  |
| FeesCollection_Details.IsIncludedInLumpSum | 1 | COL_HALLUC | FeesCollection_Details (no similar col)  |
| StudentAcademicDetail.InstallmentPlanName | 1 | COL_HALLUC | StudentAcademicDetail (no similar col)  |
| FeesCollection.Gross_Amount | 1 | COL_HALLUC | FeesCollection.FromMonth/FromMonthName  |
| FeesCollection.NetPay | 1 | COL_HALLUC | FeesCollection (no similar col)  |
| FeesCollection.FeesType_Name | 1 | COL_HALLUC | FeesCollection.CollectionType_Name/Collected_By_Name/ChequeStatus_Name  |
| FeesCollection.Role_ID | 1 | COL_HALLUC | FeesCollection.Deleted_ID/Collected_By_ID/Class_ID  |
| FeesCollection_Details.IsIncludedInLumpsum | 1 | COL_HALLUC | FeesCollection_Details (no similar col)  |

## 6. Retried with ZERO hint coverage (HINT_MAP gaps on attempt-1)
- id=594 FAIL_BOTH: u1=['ParentComplaint_Master'] u2=['ParentComplaint_Master']
- id=590 FAIL_BOTH: u1=['PerformanceAppraisalPeriod', 'PerformanceAppraisal_Details', 'PerformanceAppraisal_Master', 'PerformanceScaleDetails', 'PerformanceScaleMaster'] u2=['PerformanceAppraisal_Details', 'StaffDesignationMaster.DesignationName', 'Staff_Master.DesignationID']
- id=543 FAIL_BOTH: u1=['Student_Master.CommunicationPinCode'] u2=['Student_Master.CommunicationPinCode']
- id=510 FAIL_BOTH: u1=['Student_Master.CityName'] u2=['Student_Master.CityName']
- id=292 FAIL_BOTH: u1=['StudentAcademicDetail.InstallmentPlanName'] u2=['StudentAcademicDetail.InstallmentPlanName']

## 7. Domain-absent candidates not covered by v2.1 DOMAIN_ABSENT_TABLES
   1x  Fuel_Consumption_Details  (family: fuel)
   1x  ParentComplaint_Master  (family: complaint)
   1x  PerformanceAppraisal_Details  (family: appraisal)

## 8. PASS_RETRY profile (15 questions - proof hints work when coverage is complete)
- id=346 hints=1 u1=1 (23+19s)
- id=587 hints=2 u1=2 (21+25s)
- id=579 hints=2 u1=1 (20+25s)
- id=572 hints=2 u1=2 (19+21s)
- id=566 hints=2 u1=3 (19+20s)
- id=546 hints=2 u1=2 (21+26s)
- id=514 hints=2 u1=2 (14+22s)
- id=477 hints=2 u1=2 (10+24s)
- id=299 hints=2 u1=1 (10+13s)
- id=291 hints=2 u1=2 (18+21s)
- id=350 hints=3 u1=2 (14+24s)
- id=578 hints=4 u1=4 (21+27s)
- id=525 hints=4 u1=1 (21+21s)
- id=406 hints=4 u1=1 (19+24s)
- id=388 hints=5 u1=3 (20+27s)

## 9. Attempt-2 identifiers where table AND column both exist (validator mismatch): 0

